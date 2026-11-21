// The tutor's post office.
//
// The site cannot call Claude itself: the owner's Claude subscription may only be used by Claude Code. So a small
// relay runs on a machine where Claude Code is signed in (relay/tutor_relay.py). The lesson page posts a question
// here; the relay, which keeps one request open to this room, receives it at once, asks Claude Code with every tool
// switched off, and posts the answer back. This Worker never sees a Claude credential.
//
// One Durable Object holds the queue in memory. A Durable Object, not KV, because KV can take a minute to show a
// write to another part of the world, and a question should reach the relay in milliseconds.

const HOLD = 25_000;            // how long a waiting request is held open before it is told "nothing yet"
const KEEP = 10 * 60_000;       // a question and its answer are forgotten after ten minutes
const ALIVE = 45_000;           // the relay counts as connected if it asked for work this recently
export const LIMITS = { question: 2000, context: 14000, turns: 8, turn: 3000, perDay: 200, answer: 12000 };

const reply = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const str = (x, max) => (typeof x === "string" ? Array.from(x).slice(0, max).join("") : "");

export class TutorRoom {
  constructor() {
    this.queue = [];              // ids waiting for the relay
    this.items = new Map();       // id -> { payload, at, answer?, error? }
    this.relayWaiting = [];       // resolvers of relay requests that are being held open
    this.askers = new Map();      // id -> resolvers of browser requests waiting for that answer
    this.seen = 0;                // when the relay last asked for work
    this.day = ""; this.count = 0;
  }
  sweep(now) { for (const [id, it] of this.items) if (now - it.at > KEEP) { this.items.delete(id); this.askers.delete(id); } this.queue = this.queue.filter((id) => this.items.has(id)); }
  status(now) { return { online: now - this.seen < ALIVE, queued: this.queue.length }; }

  async fetch(req) {
    const url = new URL(req.url), now = Date.now();
    this.sweep(now);

    if (url.pathname === "/status") return reply(this.status(now));

    if (url.pathname === "/ask" && req.method === "POST") {
      const body = await req.json().catch(() => null);
      const question = str(body?.question, LIMITS.question).trim();
      if (!question) return reply({ error: "empty" }, 400);
      if (!this.status(now).online) return reply({ error: "offline" }, 503);
      const day = new Date(now).toISOString().slice(0, 10);
      if (day !== this.day) { this.day = day; this.count = 0; }
      if (++this.count > LIMITS.perDay) return reply({ error: "limit" }, 429);       // a runaway page must not drain the subscription
      const history = (Array.isArray(body.history) ? body.history : []).slice(-LIMITS.turns)
        .map((t) => ({ role: t?.role === "tutor" ? "tutor" : "me", text: str(t?.text, LIMITS.turn) })).filter((t) => t.text);
      const id = crypto.randomUUID();
      this.items.set(id, { at: now, payload: { id, question, context: str(body.context, LIMITS.context), history } });
      const waiting = this.relayWaiting.shift();
      if (waiting) waiting(id); else this.queue.push(id);
      return reply({ id });
    }

    if (url.pathname === "/answer" && req.method === "GET") {              // the lesson page, waiting
      const id = url.searchParams.get("id"), it = this.items.get(id);
      if (!it) return reply({ error: "unknown" }, 404);
      if (it.answer == null && it.error == null) {
        await new Promise((res) => { const list = this.askers.get(id) || []; list.push(res); this.askers.set(id, list); setTimeout(res, HOLD); });
      }
      if (it.error != null) return reply({ error: it.error });
      return it.answer != null ? reply({ text: it.answer }) : reply({ pending: true });
    }

    if (url.pathname === "/next" && req.method === "GET") {                 // the relay, asking for work
      this.seen = now;
      // The relay answers one question at a time and only asks for work when it is idle. So a question that was
      // handed out a while ago and never answered was lost on the way (the relay restarted, the line dropped):
      // hand it out again, once.
      const lost = [...this.items.entries()].find(([, it]) => it.handed && it.answer == null && it.error == null && now - it.handed > 20_000 && it.tries < 2);
      let id = lost ? lost[0] : this.queue.shift();
      if (!id) {
        let mine;
        id = await new Promise((res) => { mine = res; this.relayWaiting.push(res); setTimeout(() => res(null), HOLD); });
        this.relayWaiting = this.relayWaiting.filter((r) => r !== mine);
        this.seen = Date.now();
      }
      const it = id && this.items.get(id);
      if (!it) return new Response(null, { status: 204 });
      it.handed = Date.now(); it.tries = (it.tries || 0) + 1;
      return reply(it.payload);
    }

    if (url.pathname === "/answer" && req.method === "POST") {             // the relay, delivering
      const body = await req.json().catch(() => null), it = this.items.get(body?.id);
      if (!it) return reply({ error: "unknown" }, 404);
      if (typeof body.error === "string" && body.error) it.error = str(body.error, 300); else it.answer = str(body.text, LIMITS.answer);
      for (const res of this.askers.get(body.id) || []) res();
      this.askers.delete(body.id);
      return reply({ ok: true });
    }
    return reply({ error: "not found" }, 404);
  }
}

const room = (env) => env.TUTOR.get(env.TUTOR.idFromName("room"));
const forward = (env, path, init) => room(env).fetch(new Request("https://room" + path, init));

/** Routes for the signed-in owner. Returns null when the path is not the tutor's. */
export async function tutorForOwner(req, env, url) {
  const p = url.pathname;
  if (!p.startsWith("/api/tutor/")) return null;
  if (!env.TUTOR || !env.RELAY_SECRET) return p === "/api/tutor/status" ? reply({ online: false, off: true }) : reply({ error: "offline" }, 503);
  if (p === "/api/tutor/status" && req.method === "GET") return forward(env, "/status");
  if (p === "/api/tutor/answer" && req.method === "GET") return forward(env, "/answer?id=" + encodeURIComponent(url.searchParams.get("id") || ""));
  if (p === "/api/tutor/ask" && req.method === "POST") {
    // a browser will not send this header cross-site without a preflight, which is never answered
    if (!(req.headers.get("content-type") || "").includes("application/json")) return reply({ error: "content-type" }, 415);
    const buf = await req.arrayBuffer();
    if (buf.byteLength > 64 * 1024) return reply({ error: "too large" }, 413);
    return forward(env, "/ask", { method: "POST", headers: { "content-type": "application/json" }, body: buf });
  }
  return reply({ error: "not found" }, 404);
}

/** Routes for the relay: no cookie, a long random secret instead. `same` is a constant-time comparison. */
export async function tutorForRelay(req, env, url, same) {
  const p = url.pathname;
  if (!p.startsWith("/api/relay/")) return null;
  if (!env.TUTOR || !env.RELAY_SECRET) return reply({ error: "not found" }, 404);
  const given = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  if (!given || !same(given, env.RELAY_SECRET)) return reply({ error: "forbidden" }, 403);
  if (p === "/api/relay/next" && req.method === "GET") return forward(env, "/next");
  if (p === "/api/relay/answer" && req.method === "POST") {
    const buf = await req.arrayBuffer();
    if (buf.byteLength > 128 * 1024) return reply({ error: "too large" }, 413);
    return forward(env, "/answer", { method: "POST", headers: { "content-type": "application/json" }, body: buf });
  }
  return reply({ error: "not found" }, 404);
}
