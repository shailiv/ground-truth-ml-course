// Ground Truth - the whole site sits behind this Worker.
//   1. Who is this?  Cloudflare Access (if ACCESS_TEAM + ACCESS_AUD are set) or a passphrase cookie.
//   2. /api/progress  GET / PUT  - one JSON document per person in KV, merged field by field (public/js/merge.js).
//   3. /api/tutor/*   the in-page tutor: questions wait here for the relay that runs Claude Code (tutor.js).
//   4. everything else - static files, served only to a signed-in visitor.
import { merge, clamp } from "./public/js/merge.js";
import { TutorRoom, tutorForOwner, tutorForRelay } from "./tutor.js";
export { TutorRoom };

const COOKIE = "gt_session";
const SESSION_DAYS = 60;
const MAX_BODY = 512 * 1024;
const CSP = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; media-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'";

/** Every response leaves through here, so none can miss the security headers. */
function secure(res, extra = {}) {
  const h = new Headers(res.headers);
  h.set("x-content-type-options", "nosniff");
  h.set("referrer-policy", "same-origin");
  h.set("x-frame-options", "DENY");
  h.set("content-security-policy", CSP);
  if (!h.has("cache-control")) h.set("cache-control", "no-store");
  for (const [k, v] of Object.entries(extra)) h.set(k, v);
  return new Response(res.body, { status: res.status, headers: h });
}
const json = (data, status = 200) => secure(new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } }));
const redirect = (to, headers = {}) => secure(new Response(null, { status: 303, headers: { location: to, "cache-control": "no-store", ...headers } }));
const text = (msg, status) => secure(new Response(msg, { status, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" } }));

// ---------- passphrase sessions (HMAC-signed cookie) ----------
const enc = new TextEncoder();
const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return b64u(await crypto.subtle.sign("HMAC", key, enc.encode(msg)));
}
function safeEqual(a, b) {
  const x = enc.encode(a), y = enc.encode(b);
  let diff = x.length ^ y.length;
  for (let i = 0; i < Math.max(x.length, y.length); i++) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}
// The signing key depends on the passphrase too: changing the passphrase signs every device out.
const sessionKey = (env) => env.SESSION_SECRET + "\n" + env.PASSPHRASE;
async function sessionCookie(env) {
  const exp = Date.now() + SESSION_DAYS * 864e5;
  return `${COOKIE}=${exp}.${await hmac(sessionKey(env), "owner." + exp)}; Path=/; Max-Age=${SESSION_DAYS * 86400}; HttpOnly; Secure; SameSite=Lax`;
}
async function cookieUser(req, env) {
  const m = (req.headers.get("cookie") || "").match(new RegExp(`(?:^|;\\s*)${COOKIE}=(\\d+)\\.([\\w-]+)`));
  if (!m || +m[1] < Date.now() || !env.SESSION_SECRET || !env.PASSPHRASE) return null;
  if (!safeEqual(m[2], await hmac(sessionKey(env), "owner." + m[1]))) return null;
  return { user: "owner", renew: +m[1] - Date.now() < (SESSION_DAYS / 2) * 864e5 };      // slide the session while it is in use
}

// ---------- Cloudflare Access (verifies the signed token Access attaches to every request) ----------
let jwks = { at: 0, keys: {} };
async function accessUser(req, env) {
  const token = req.headers.get("cf-access-jwt-assertion");
  if (!token) return null;
  try {
    const [h, p, sig] = token.split(".");
    const dec = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
    const head = JSON.parse(new TextDecoder().decode(dec(h))), body = JSON.parse(new TextDecoder().decode(dec(p)));
    if (head.alg !== "RS256") return null;
    if (!jwks.keys[head.kid] && Date.now() - jwks.at > 60e3 || Date.now() - jwks.at > 3600e3) {     // refresh hourly, or once a minute for an unknown key
      try {
        const r = await fetch(`https://${env.ACCESS_TEAM}.cloudflareaccess.com/cdn-cgi/access/certs`);
        if (r.ok) jwks = { at: Date.now(), keys: Object.fromEntries((await r.json()).keys.map((k) => [k.kid, k])) };
        else jwks.at = Date.now();
      } catch { jwks.at = Date.now(); }             // keep the keys we have if the fetch fails
    }
    const jwk = jwks.keys[head.kid];
    if (!jwk) return null;
    const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, dec(sig), enc.encode(`${h}.${p}`));
    const aud = [].concat(body.aud || []), nowS = Date.now() / 1000;
    if (!ok || !aud.includes(env.ACCESS_AUD) || typeof body.exp !== "number" || body.exp < nowS || (typeof body.nbf === "number" && body.nbf > nowS + 60)) return null;
    if (body.iss !== `https://${env.ACCESS_TEAM}.cloudflareaccess.com`) return null;
    const who = String(body.email || body.sub || "").toLowerCase().replace(/[^a-z0-9@._+-]/g, "");
    return who ? { user: who } : null;
  } catch { return null; }
}

const usesAccess = (env) => !!(env.ACCESS_TEAM && env.ACCESS_AUD);
const whoIs = (req, env) => (usesAccess(env) ? accessUser(req, env) : cookieUser(req, env));

// Two brakes on passphrase guessing: Cloudflare's rate limiter when it is bound (all addresses together), and a small
// per-address memory in this isolate. The passphrase itself is long and random, so these are belt and braces.
const tries = new Map();
function throttled(ip) {
  const now = Date.now(), t = (tries.get(ip) || []).filter((x) => now - x < 10 * 60e3);
  if (tries.size > 2000) for (const k of [...tries.keys()].slice(0, 1000)) tries.delete(k);       // forget the oldest, never everyone
  tries.set(ip, t);
  return t.length >= 8;
}
const failed = (ip) => { const t = tries.get(ip) || []; t.push(Date.now()); tries.set(ip, t); };

async function login(req, env) {
  const ip = req.headers.get("cf-connecting-ip") || "?";
  if (req.method !== "POST") return secure(await env.ASSETS.fetch(new Request(new URL("/login.html", req.url))), { "cache-control": "no-store" });
  if (throttled(ip)) return text("Too many attempts. Wait ten minutes.", 429);
  if (env.LOGIN_LIMIT) { const { success } = await env.LOGIN_LIMIT.limit({ key: "login" }); if (!success) return text("Too many attempts. Wait a minute.", 429); }
  const form = await req.formData().catch(() => null);
  const given = String(form?.get("passphrase") || "").trim();
  if (!env.PASSPHRASE || !env.SESSION_SECRET || !safeEqual(given, env.PASSPHRASE)) {
    failed(ip);
    await new Promise((r) => setTimeout(r, 400));
    return redirect("/login?wrong=1");              // the page reads ?wrong; a deep link in the #fragment survives the redirect
  }
  return redirect("/", { "set-cookie": await sessionCookie(env) });
}

async function progress(req, env, user, url) {
  const key = `progress:${user}`, undoKey = `backup:${user}:before-reset`;
  const now = Date.now();
  const reply = async (state, status = 200) => json({ state, user, now, undo: (await env.PROGRESS.get(undoKey, "json"))?.at || 0 }, status);
  if (url.pathname === "/api/progress/restore") {
    if (req.method !== "POST") return json({ error: "method" }, 405);
    const saved = await env.PROGRESS.get(undoKey, "json");
    if (!saved?.state) return json({ error: "nothing to restore" }, 404);
    // bring the copy back with fresh timestamps, so the reset every device still remembers cannot delete it again
    const st = merge(null, saved.state);
    for (const c of ["lessons", "cards", "cases", "labs", "days", "missions"]) for (const rec of Object.values(st[c])) rec.t = now;
    const cur = (await env.PROGRESS.get(key, "json")) || {};
    st.settings = { ...st.settings, ...(cur.settings || {}), t: now };
    await env.PROGRESS.put(key, JSON.stringify(st));
    await env.PROGRESS.delete(undoKey);
    return json({ state: st, user, now, undo: 0 });
  }
  if (req.method === "GET") return reply((await env.PROGRESS.get(key, "json")) || null);
  if (req.method !== "PUT") return json({ error: "method" }, 405);
  // a browser will not send this header cross-site without a preflight, which we never answer
  if (!(req.headers.get("content-type") || "").includes("application/json")) return json({ error: "content-type" }, 415);
  if (+(req.headers.get("content-length") || 0) > MAX_BODY) return json({ error: "too large" }, 413);
  const buf = await req.arrayBuffer();
  if (buf.byteLength > MAX_BODY) return json({ error: "too large" }, 413);
  let incoming;
  try { incoming = JSON.parse(new TextDecoder().decode(buf)).state; } catch { return json({ error: "bad json" }, 400); }
  if (!incoming || typeof incoming !== "object") return json({ error: "no state" }, 400);
  clamp(incoming, now);                               // no timestamp from a device may lie in the future
  const current = await env.PROGRESS.get(key, "json");
  // a "start over" is about to wipe what is stored: keep a copy first, so it can be undone
  if (current && (incoming.settings?.reset || 0) > (current.settings?.reset || 0) && Object.keys(current.lessons || {}).length + Object.keys(current.cards || {}).length > 0) {
    await env.PROGRESS.put(undoKey, JSON.stringify({ at: now, state: current }));
  }
  const merged = merge(current, incoming);
  const out = JSON.stringify(merged);
  if (out.length > 2 * MAX_BODY) return json({ error: "too large" }, 413);
  await env.PROGRESS.put(key, out);
  const day = new Date().toISOString().slice(0, 10);                  // one dated copy per day, kept 45 days
  if (current && !(await env.PROGRESS.get(`backup:${user}:${day}`))) {
    await env.PROGRESS.put(`backup:${user}:${day}`, JSON.stringify(current), { expirationTtl: 45 * 86400 });
  }
  return reply(merged);
}

/** Audio must answer byte-range requests (Safari will not play or seek without them); the asset server may not. */
async function ranged(req, res, h) {
  const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.get("range") || "");
  h.set("accept-ranges", "bytes");
  if (!m || res.status !== 200 || (!m[1] && !m[2])) return null;
  const buf = await res.arrayBuffer(), size = buf.byteLength;
  const start = m[1] ? +m[1] : Math.max(0, size - +m[2]), end = m[1] && m[2] ? Math.min(+m[2], size - 1) : size - 1;
  if (start >= size || start > end) return new Response(null, { status: 416, headers: { "content-range": `bytes */${size}` } });
  h.set("content-range", `bytes ${start}-${end}/${size}`);
  h.set("content-length", String(end - start + 1));
  return new Response(buf.slice(start, end + 1), { status: 206, headers: h });
}

const PUBLIC = new Set(["/login.html", "/css/app.css", "/css/fonts.css", "/img/mark.svg", "/img/contours.svg", "/favicon.svg", "/js/login.js"]);
const isOpen = (path) => PUBLIC.has(path) || /^\/fonts\/[A-Za-z0-9_-]+\.woff2$/.test(path);

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const path = url.pathname;
    if (/%2f|%5c|%2e|\\|\/\.\.?(\/|$)/i.test(path)) return text("Bad path", 400);       // no encoded slashes or dot segments, on any runtime
    if (path === "/login" && !usesAccess(env)) return login(req, env);
    if (path === "/logout") {
      if (req.method !== "POST") return redirect("/");                                    // a link from another site cannot sign you out
      return redirect("/login", { "set-cookie": `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax` });
    }
    if (path.startsWith("/api/relay/")) {                                                 // the tutor relay: its own secret, no cookie
      const ip = req.headers.get("cf-connecting-ip") || "?";
      if (throttled(ip)) return text("Too many attempts. Wait ten minutes.", 429);
      const res = await tutorForRelay(req, env, url, safeEqual);
      if (res.status === 403) failed(ip);
      return secure(res);
    }
    const open = isOpen(path);
    const who = open ? null : await whoIs(req, env);
    if (!open && !who) {
      if (path.startsWith("/api/")) return json({ error: "signed out" }, 401);
      return usesAccess(env) ? text("Not signed in.", 401) : redirect("/login");
    }
    const renew = who?.renew ? { "set-cookie": await sessionCookie(env) } : {};
    if (path === "/api/progress" || path === "/api/progress/restore") return secure(await progress(req, env, who.user, url), renew);
    if (path === "/api/me") return json({ user: who.user });
    if (path.startsWith("/api/tutor/")) return secure(await tutorForOwner(req, env, url), renew);
    if (path.startsWith("/api/")) return json({ error: "not found" }, 404);
    // files are served at their exact paths (html_handling is "none"), so the one alias is spelled out here
    const res = await env.ASSETS.fetch(path === "/" ? new Request(new URL("/index.html", req.url), req) : req);
    const h = new Headers(res.headers);
    const media = /\.(mp3|woff2|png|jpg|svg)$/.test(path);
    // clip names carry a hash of their words, so a clip never changes: cache it for good. Never cache an error.
    if (!open) h.set("cache-control", !res.ok ? "no-store" : /\/audio\/.+\.mp3$/.test(path) ? "private, max-age=31536000, immutable" : media ? "private, max-age=86400" : "private, no-cache");
    let out = null;
    if (path.endsWith(".mp3")) out = await ranged(req, res, h);
    return secure(out || new Response(res.body, { status: res.status, headers: h }), renew);
  },
};
