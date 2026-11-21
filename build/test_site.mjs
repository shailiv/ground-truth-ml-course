// Tests for the two things that would hurt most if they broke: the progress merge, and the lock on the site.
//   node build/test_site.mjs            (runs the real worker.js against the local stand-in for Cloudflare)
import fs from "node:fs";
import worker from "../site/worker.js";
import { merge, clamp, blank } from "../site/public/js/merge.js";
import { makeEnv } from "./local_env.mjs";

let pass = 0, fail = 0;
const ok = (cond, name) => { if (cond) pass++; else { fail++; console.log("FAIL  " + name); } };
const eq = (a, b, name) => ok(JSON.stringify(a) === JSON.stringify(b), `${name}: got ${JSON.stringify(a)}, wanted ${JSON.stringify(b)}`);

// ---------------------------------------------------------------- merge
{
  const T = 1_700_000_000_000;
  // the laptop finished the lesson at noon; a phone tab open since morning writes its position later
  const laptop = { ...blank(), lessons: { "1-1": { guess: 2, watched: T + 100, quiz: { score: 3, of: 4, t: T + 200 }, done: T + 200, seg: 0, t: T + 200 } } };
  const phone = { ...blank(), lessons: { "1-1": { guess: 1, seg: 4, t: T + 900 } } };
  for (const [a, b, tag] of [[laptop, phone, "laptop,phone"], [phone, laptop, "phone,laptop"]]) {
    const m = merge(a, b).lessons["1-1"];
    eq(m.done, T + 200, `a stale tab cannot un-finish a lesson (${tag})`);
    eq(m.watched, T + 100, `watched stays (${tag})`);
    eq(m.quiz?.score, 3, `quiz stays (${tag})`);
    eq(m.seg, 4, `position follows the device that moved last (${tag})`);
    eq(m.guess, 2, `the first guess is kept (${tag})`);
  }
  eq(merge(laptop, phone), merge(phone, laptop), "merge is the same in either order");
  eq(merge(merge(laptop, phone), phone), merge(laptop, phone), "merging twice changes nothing");
  // cards: the copy answered more often wins, even if the other was written later
  const c1 = { ...blank(), cards: { "1-1-c0": { box: 2, n: 3, ok: 3, due: 5, t: T } } }, c2 = { ...blank(), cards: { "1-1-c0": { box: 0, n: 1, ok: 0, due: 9, t: T + 50 } } };
  eq(merge(c1, c2).cards["1-1-c0"].n, 3, "the card answered more times wins");
  // a later retake of the quiz replaces the earlier score
  const q1 = { ...blank(), lessons: { "2-1": { quiz: { score: 1, of: 4, t: T }, t: T } } }, q2 = { ...blank(), lessons: { "2-1": { quiz: { score: 4, of: 4, t: T + 9 }, t: T + 9 } } };
  eq(merge(q2, q1).lessons["2-1"].quiz.score, 4, "the latest quiz attempt wins");
  // start over: records from before the reset disappear on every device, later ones survive, settings stay
  const before = { ...blank(), lessons: { "1-1": { done: T, t: T }, "1-2": { done: T + 500, t: T + 500 } }, settings: { dailyCap: 6, t: T } };
  const reset = { ...blank(), settings: { dailyCap: 6, reset: T + 300, t: T + 300 } };
  const r = merge(before, reset);
  ok(!r.lessons["1-1"] && r.lessons["1-2"], "a reset drops what came before it and keeps what came after");
  eq(r.settings.dailyCap, 6, "settings survive a reset");
  // hostile or broken input
  const bad = JSON.parse('{"lessons":{"__proto__":{"done":1,"t":1},"1-1":"oops","1-2":{"done":5,"t":5}},"cards":[1,2],"settings":7}');
  const mb = merge(blank(), bad);
  ok(mb.lessons["1-2"]?.done === 5 && !("1-1" in mb.lessons) && ({}).done === undefined, "broken records are skipped and the prototype is untouched");
  eq(merge(null, undefined), blank(), "merging nothing gives a blank state");
  // the server never lets a device's clock put anything in the future
  const now = T + 1000, fut = clamp({ ...blank(), lessons: { "1-1": { done: now + 9e9, t: now + 9e9, quiz: { t: now + 9e9 } } }, cards: { x: { due: now + 9e9, t: now - 5 } }, settings: { reset: now + 9e9, t: now + 9e9 } }, now);
  ok(fut.lessons["1-1"].done === now && fut.lessons["1-1"].t === now && fut.lessons["1-1"].quiz.t === now && fut.settings.reset === now, "future timestamps are pulled back to now");
  eq(fut.cards.x.due, now + 9e9, "a card's due date may be in the future");
}

// ---------------------------------------------------------------- the worker: locked, and correct once inside
const env = makeEnv();
const call = (path, init = {}) => worker.fetch(new Request("http://localhost" + path, { redirect: "manual", ...init, headers: { "cf-connecting-ip": "10.0.0.1", ...(init.headers || {}) } }), env);
const form = (o) => ({ method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" }, body: new URLSearchParams(o).toString() });
const clip = (() => { const d = "site/public/audio"; if (!fs.existsSync(d)) return null; for (const l of fs.readdirSync(d)) for (const f of fs.readdirSync(`${d}/${l}`)) if (f.endsWith(".mp3")) return `/audio/${l}/${f}`; return null; })();
{
  // signed out: nothing of the course is readable
  for (const p of ["/", "/index.html", "/data/course.json", "/data/assistant-pack.md", "/js/app.js", "/js/merge.js", "/reports/plain.html", clip].filter(Boolean)) {
    const r = await call(p);
    ok(r.status === 303 && r.headers.get("location") === "/login", `signed out, ${p} redirects to the sign-in page (got ${r.status})`);
  }
  eq((await call("/api/progress")).status, 401, "signed out, the progress API answers 401");
  eq((await call("/api/progress", { method: "PUT", headers: { "content-type": "application/json" }, body: "{}" })).status, 401, "signed out, nothing can be written");
  for (const p of ["/fonts/..%2fdata/course.json", "/fonts/%2e%2e/data/course.json", "/css/..%5cdata/course.json", "/fonts/../data/course.json"]) {
    const r = await call(p);
    ok([400, 303, 404].includes(r.status) && !(await r.text()).includes("lessons"), `no way round through ${p} (got ${r.status})`);
  }
  for (const p of ["/login", "/login.html", "/css/app.css", "/js/login.js", "/favicon.svg"]) eq((await call(p)).status, 200, `the sign-in page can load ${p}`);
  const page = await call("/login");
  ok((page.headers.get("content-security-policy") || "").includes("default-src"), "every response carries the content-security policy");
  eq(page.headers.get("x-frame-options"), "DENY", "the site cannot be framed");

  // signing in
  const wrong = await call("/login", form({ passphrase: "nope" }));
  ok(wrong.status === 303 && wrong.headers.get("location") === "/login?wrong=1" && !wrong.headers.get("set-cookie"), "a wrong passphrase gets no cookie");
  const right = await call("/login", form({ passphrase: "test" }));
  const cookie = (right.headers.get("set-cookie") || "").split(";")[0];
  ok(right.status === 303 && right.headers.get("location") === "/" && /HttpOnly/.test(right.headers.get("set-cookie")) && /Secure/.test(right.headers.get("set-cookie")), "the right passphrase sets a locked-down cookie");
  const me = (init = {}) => ({ ...init, headers: { cookie, ...(init.headers || {}) } });
  eq((await call("/", me())).status, 200, "signed in, the course opens");
  eq((await call("/", { headers: { cookie: cookie.slice(0, -3) + "abc" } })).status, 303, "a tampered cookie is refused");
  const other = makeEnv({ PASSPHRASE: "changed" });
  eq((await worker.fetch(new Request("http://localhost/", { headers: { cookie }, redirect: "manual" }), other)).status, 303, "changing the passphrase signs every device out");

  // progress: write, read back, merge, start over, undo
  const put = (state) => call("/api/progress", me({ method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ state }) }));
  const now = Date.now();
  let r = await put({ ...blank(), lessons: { "1-1": { done: now - 5000, watched: now - 6000, t: now - 5000 } }, cards: { "1-1-c0": { box: 1, n: 1, ok: 1, due: now + 864e5, t: now - 5000 } } });
  eq(r.status, 200, "progress is accepted");
  r = await put({ ...blank(), lessons: { "1-1": { seg: 3, t: now - 100 } } });                      // the stale phone tab
  let body = await r.json();
  ok(body.state.lessons["1-1"].done === now - 5000 && body.state.lessons["1-1"].seg === 3, "the server merges field by field too");
  ok(typeof body.now === "number" && body.undo === 0, "answers carry the server clock");
  eq((await call("/api/progress", me({ method: "PUT", headers: { "content-type": "text/plain" }, body: "{}" }))).status, 415, "a cross-site form cannot write progress");
  eq((await call("/api/progress", me({ method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ state: { pad: "x".repeat(600000) } }) }))).status, 413, "an oversized write is refused");
  r = await put({ ...blank(), lessons: { "9-9": { done: now + 9e10, t: now + 9e10 } } });
  ok((await r.json()).state.lessons["9-9"].t <= Date.now() + 1000, "a device with a fast clock cannot write the future");
  await new Promise((res) => setTimeout(res, 5));                    // "start over" is pressed later than the last answer, never in the same millisecond
  r = await put({ ...blank(), settings: { reset: Date.now(), t: Date.now() } });
  body = await r.json();
  ok(Object.keys(body.state.lessons).length === 0 && body.undo > 0, "start over clears the record and keeps an undo copy");
  r = await call("/api/progress/restore", me({ method: "POST", headers: { "content-type": "application/json" }, body: "{}" }));
  body = await r.json();
  ok(r.status === 200 && body.state.lessons["1-1"]?.done && body.undo === 0, "undo brings the progress back");
  body = await (await call("/api/progress", me())).json();
  ok(body.state.lessons["1-1"]?.done && body.state.cards["1-1-c0"], "and it stays back after the next read");
  eq((await call("/api/progress/restore", me({ method: "POST", headers: { "content-type": "application/json" }, body: "{}" }))).status, 404, "there is nothing to undo twice");

  // audio: byte ranges, as Safari needs them
  if (clip) {
    const full = await call(clip, me()), size = (await full.arrayBuffer()).byteLength;
    ok(full.status === 200 && full.headers.get("accept-ranges") === "bytes" && /immutable/.test(full.headers.get("cache-control")), "a clip is served whole, cacheable");
    const part = await call(clip, me({ headers: { range: "bytes=100-199" } }));
    ok(part.status === 206 && part.headers.get("content-range") === `bytes 100-199/${size}` && (await part.arrayBuffer()).byteLength === 100, "a byte range gets exactly that range");
    const tail = await call(clip, me({ headers: { range: "bytes=-50" } }));
    ok(tail.status === 206 && (await tail.arrayBuffer()).byteLength === 50, "a suffix range works");
    const open = await call(clip, me({ headers: { range: "bytes=0-" } }));
    ok(open.status === 206 && open.headers.get("content-range") === `bytes 0-${size - 1}/${size}`, "an open-ended range works");
    eq((await call(clip, me({ headers: { range: `bytes=${size + 5}-` } }))).status, 416, "a range past the end is refused");
  } else console.log("note: no audio on disk, range tests skipped");

  // the tutor: a question travels page -> room -> relay -> room -> page, and nobody without the secret can listen in
  {
    const J = { "content-type": "application/json" }, relayAuth = { authorization: "Bearer test-relay" };
    const askBody = (o) => me({ method: "POST", headers: J, body: JSON.stringify(o) });
    eq((await call("/api/tutor/status")).status, 401, "signed out, the tutor is closed");
    eq((await call("/api/tutor/ask", { method: "POST", headers: J, body: "{}" })).status, 401, "signed out, nobody can ask");
    eq((await (await call("/api/tutor/status", me())).json()).online, false, "with no relay connected the tutor says so");
    eq((await call("/api/tutor/ask", askBody({ question: "hello" }))).status, 503, "and a question is refused, so the page can fall back");
    eq((await call("/api/relay/next")).status, 403, "the relay door needs its secret");
    eq((await call("/api/relay/next", { headers: { authorization: "Bearer wrong" } })).status, 403, "a wrong relay secret is refused");
    eq((await call("/api/relay/next", me())).status, 403, "the owner's cookie does not open the relay door");
    const waiting = call("/api/relay/next", { headers: relayAuth });                   // the relay, holding a request open
    await new Promise((res) => setTimeout(res, 20));
    eq((await (await call("/api/tutor/status", me())).json()).online, true, "a waiting relay shows as connected");
    eq((await call("/api/tutor/ask", askBody({ question: "   " }))).status, 400, "an empty question is refused");
    eq((await call("/api/tutor/ask", me({ method: "POST", headers: { "content-type": "text/plain" }, body: "{}" }))).status, 415, "a cross-site form cannot ask");
    const asked = await call("/api/tutor/ask", askBody({ question: "Why split by time? " + "x".repeat(5000), context: "Lesson 2-1 ...", history: [{ role: "me", text: "earlier" }, { role: "tutor", text: "reply" }, { role: "hacker", text: 7 }] }));
    const { id } = await asked.json();
    ok(asked.status === 200 && typeof id === "string", "a question is accepted");
    const got = await (await waiting).json();
    ok(got.id === id && got.question.length === 2000 && got.context === "Lesson 2-1 ..." && got.history.length === 2 && got.history[1].role === "tutor", "the relay receives it at once, trimmed to the limits");
    const pending = call("/api/tutor/answer?id=" + id, me());                         // the page, waiting for the answer
    await new Promise((res) => setTimeout(res, 20));
    eq((await call("/api/relay/answer", { method: "POST", headers: { ...J, ...relayAuth }, body: JSON.stringify({ id, text: "Because the future is what you will be scored on." }) })).status, 200, "the relay delivers the answer");
    eq((await (await pending).json()).text, "Because the future is what you will be scored on.", "and the waiting page gets it");
    eq((await call("/api/tutor/answer?id=" + id)).status, 401, "signed out, an answer cannot be read");
    eq((await call("/api/tutor/answer?id=nope", me())).status, 404, "an unknown question id is 404");
    // a failure on the relay's side reaches the page as a message, not as silence
    const w2 = call("/api/relay/next", { headers: relayAuth });
    await new Promise((res) => setTimeout(res, 20));
    const id2 = (await (await call("/api/tutor/ask", askBody({ question: "second" }))).json()).id;
    await w2;
    await call("/api/relay/answer", { method: "POST", headers: { ...J, ...relayAuth }, body: JSON.stringify({ id: id2, error: "The tutor could not answer just now." }) });
    eq((await (await call("/api/tutor/answer?id=" + id2, me())).json()).error, "The tutor could not answer just now.", "a relay failure is passed on");
    const bare = makeEnv({ TUTOR: undefined, RELAY_SECRET: undefined });
    const c2 = (await worker.fetch(new Request("http://localhost/login", { ...form({ passphrase: "test" }), redirect: "manual" }), bare)).headers.get("set-cookie").split(";")[0];
    eq((await (await worker.fetch(new Request("http://localhost/api/tutor/status", { headers: { cookie: c2 } }), bare)).json()).online, false, "a site deployed without the tutor simply reports it offline");
    eq((await worker.fetch(new Request("http://localhost/api/relay/next", { headers: relayAuth }), bare)).status, 404, "and has no relay door at all");
  }

  // signing out
  ok((await call("/logout", me())).headers.get("set-cookie") == null, "a link cannot sign you out");
  ok(/Max-Age=0/.test((await call("/logout", me({ method: "POST" }))).headers.get("set-cookie") || ""), "the sign-out button does");
  eq((await call("/api/nothing", me())).status, 404, "unknown API paths are 404");

  // brute force: the ninth wrong try from one address is refused
  let last;
  for (let i = 0; i < 9; i++) last = await worker.fetch(new Request("http://localhost/login", { ...form({ passphrase: "x" + i }), redirect: "manual", headers: { "content-type": "application/x-www-form-urlencoded", "cf-connecting-ip": "10.9.9.9" } }), env);
  eq(last.status, 429, "repeated wrong passphrases are slowed down");
}

console.log(`${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
