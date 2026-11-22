// Ground Truth - the app shell: routes, home, lesson flow, daily review, practice, field guide.
import { h } from "./visuals.js";
import { Player, parseNarration } from "./player.js";
import * as store from "./store.js";

const $ = (sel, root = document) => root.querySelector(sel);
const main = $("#main");
let course, widgetData, player;
const ctx = { widgets: async () => (widgetData ??= await (await fetch("data/widgets.json")).json()) };
const prefs = {
  get: (k) => { try { return JSON.parse(localStorage.getItem("gt.pref." + k)); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem("gt.pref." + k, JSON.stringify(v)); } catch { /* fine */ } },
};
const ICON = {
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/></svg>',
  spark: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M18 6l-2.5 2.5M8.5 15.5L6 18"/></svg>',
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>',
  done: '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="24" cy="24" r="19"/><path d="M15 24.5l6 6 12-13"/></svg>',
  pause: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4.5" width="4.2" height="15" rx="1.2"/><rect x="13.8" y="4.5" width="4.2" height="15" rx="1.2"/></svg>',
  caseFile: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4"/><path d="M14 3v5h5"/><path d="M19 8v3"/><circle cx="16.5" cy="16.5" r="3"/><path d="M19 19l2.2 2.2"/></svg>',
  lab: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4.5" width="18" height="15" rx="2.5"/><path d="M7.5 10l3 2.5-3 2.5M13 15h3.5"/></svg>',
  chev: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>',
};
const icon = (name) => { const sp = h("span", { style: { display: "inline-flex" }, "aria-hidden": "true" }); sp.innerHTML = ICON[name]; return sp.firstChild; };
const btn = (label, onclick, cls = "", ic) => h("button", { class: "btn " + cls, type: "button", onclick }, ic ? icon(ic) : null, label);
const link = (label, href, cls = "") => h("a", { class: "btn " + cls, href }, label);
const shuffle = (a) => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; } return b; };
const L = (id) => course.lessons.find((l) => l.id === id);
const lessonState = (id) => store.state.lessons[id] || {};
const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
const PRACTICE_MIN = { case: 10, lab: 20 };
const lessonMin = (l) => Math.round(l.minutes + 3);          // watching plus the four questions
// a row for a case file or a lab, used on the home page and the practice page
function practiceRow(p, meta) {
  const dn = store.state[p.kind === "case" ? "cases" : "labs"][p.id]?.done, d = h("span", { class: "dot" });
  d.innerHTML = dn ? ICON.check : ICON[p.kind === "case" ? "caseFile" : "lab"];
  return h("a", { class: "lrow case " + (dn ? "done" : ""), href: `#/${p.kind}/${p.id}` }, d, h("span", {}, h("b", { text: p.title }), h("small", { text: meta ? p.blurb : p.kind === "case" ? "Case file: audit a report an assistant wrote" : "Lab: run it with your own assistant" })),
    h("span", { class: "meta", text: meta || `${PRACTICE_MIN[p.kind]} min` }));
}
// a compact audio player in the site's own style (the browser's default one looks like a different product)
function audioCard(src, dur, label) {
  const au = new Audio(); au.preload = "none"; au.src = src;
  const tm = (t) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, "0")}`;
  const play = h("button", { class: "play", type: "button", "aria-label": "Play " + label }), time = h("span", { class: "time", text: `0:00 / ${tm(dur)}` });
  const range = h("input", { type: "range", min: 0, max: Math.round(dur), step: 1, value: 0, "aria-label": "Position in " + label, oninput: (e) => { au.currentTime = +e.target.value; } });
  const draw = () => { play.innerHTML = au.paused ? ICON.play : ICON.pause; play.setAttribute("aria-label", (au.paused ? "Play " : "Pause ") + label); };
  play.addEventListener("click", () => { player?.pause(); audioCard.current && audioCard.current !== au && audioCard.current.pause(); audioCard.current = au; au.paused ? au.play().catch(() => toast("The audio could not be played")) : au.pause(); });
  au.addEventListener("play", draw); au.addEventListener("pause", draw); au.addEventListener("ended", draw);
  au.addEventListener("timeupdate", () => { range.value = Math.floor(au.currentTime); time.textContent = `${tm(au.currentTime)} / ${tm(dur)}`; });
  const SP = [1, 1.15, 1.3, 1.5, 0.85], speed = h("button", { class: "chip", type: "button", title: "Playback speed", text: `${prefs.get("speed") || 1}×`, onclick: () => { const r = SP[(SP.indexOf(au.playbackRate) + 1) % SP.length] || 1; au.playbackRate = r; prefs.set("speed", r); speed.textContent = `${r}×`; } });
  au.playbackRate = prefs.get("speed") || 1;
  au.addEventListener("play", () => { au.playbackRate = prefs.get("speed") || 1; });
  const skip = (d, t) => h("button", { class: "chip", type: "button", text: t, "aria-label": `${d < 0 ? "Back" : "Forward"} 15 seconds`, onclick: () => { au.currentTime = Math.max(0, Math.min(dur, au.currentTime + d)); } });
  draw();
  const el = h("div", { class: "audio-card" }, play, skip(-15, "-15s"), range, skip(15, "+15s"), speed, time);
  el.stop = () => au.pause();
  return el;
}
function toast(msg) { const t = h("div", { class: "toast", role: "status", text: msg }); document.body.append(t); setTimeout(() => t.remove(), 2200); }
async function copy(text, msg = "Copied") {
  try { await navigator.clipboard.writeText(text); toast(msg); } catch { const ta = h("textarea", { style: { position: "fixed", opacity: 0 } }); ta.value = text; document.body.append(ta); ta.select(); document.execCommand("copy"); ta.remove(); toast(msg); }
}
const copyBox = (text) => h("div", { class: "copybox" }, h("p", { text }), btn("Copy", () => copy(text), "small", "copy"));

// ---------- the tutor ----------
// Claude, on the owner's own subscription, reached one of two ways. If the relay is connected (relay/tutor_relay.py:
// Claude Code on a machine of the owner's), the question is answered here on the page. If it is not, the question
// opens claude.ai in a new tab. Either way it carries the moment it was asked from: the lesson, the part and second
// of the video, the sentence being spoken, what the slide showed, and what the learner has already finished.
const WHO = "I'm a data analyst at an adtech platform (my clients are advertisers). I'm learning machine-learning fundamentals from a private course so that I can frame problems, brief an AI coding assistant and audit what it returns. I'm strong in SQL and BI, light on Python and new to ML. Be plain and concrete, use adtech examples, keep it short, and end by checking my understanding with one question.";
const mmss = (t) => `${Math.floor((t || 0) / 60)}:${String(Math.floor((t || 0) % 60)).padStart(2, "0")}`;
const cut = (text, n) => { const a = Array.from(String(text)); return a.length > n ? a.slice(0, n).join("") + " …" : a.join(""); };
const slideText = (v) => (v.type === "widget" ? `an interactive called "${v.name}"${v.title ? `, titled "${v.title}"` : ""}${v.note ? `. Its note says: ${v.note}` : ""}` : cut(JSON.stringify(v), 1800));

/** Where the learner is in the video, for a question asked while watching. */
function watchMoment(les) {
  const i = player?.i ?? 0, t = player?.t ?? 0, sg = les.segments[i], parsed = parseNarration(sg.narration);
  const f = Math.min(1, t / (player?.durs?.[i] || 1)), sn = parsed.sentences.find((x) => f >= x.from && f < x.to) || parsed.sentences.at(-1);
  return { label: `Part ${i + 1} · ${mmss(t)}`, seg: i, t,
    where: `watching the lesson, part ${i + 1} of ${les.segments.length}, ${mmss(t)} into that part${player?.playing ? "" : " (paused)"}.`,
    detail: [`The sentence being spoken at that moment: "${sn?.text || ""}"`, `That part's whole narration: "${parsed.spoken}"`, `On the slide for that part (as data): ${slideText(sg.visual)}`,
      i ? `The part just before it said: "${parseNarration(les.segments[i - 1].narration).spoken}"` : ""].filter(Boolean).join("\n\n") };
}
/** The moment a question was asked from: where in the lesson, what was on screen, how far the learner has got. */
function moment(lesson, at = {}) {
  const out = [];
  if (lesson) { const mod = course.modules.find((m) => m.n === lesson.module); out.push(`Lesson ${lesson.id}: "${lesson.title}" (${lesson.subtitle}). It is in module ${mod.n}, "${mod.title}".`); }
  if (at.where) out.push("Where I was when I asked: " + at.where);
  if (at.detail) out.push(at.detail);
  if (lesson) out.push("The lesson's three takeaways:\n- " + lesson.takeaways.join("\n- "));
  const done = course.lessons.filter((l) => lessonState(l.id).done).map((l) => l.id);
  out.push(`My progress: ${done.length} of ${course.lessons.length} lessons finished${done.length ? ` (${done.join(", ")})` : ""}. Any lesson not in that list is new to me.`);
  return out.join("\n\n");
}
/** The lesson itself, for the tutor to draw on. Identical for every question asked in the same lesson, so it can be cached. */
function lessonText(lesson) {
  const out = [];
  if (lesson) {
    out.push(`Lesson ${lesson.id}: "${lesson.title}" (${lesson.subtitle}).`);
    out.push("Words this lesson introduces: " + lesson.glossary.map((g) => `${g.term}: ${g.def}`).join(" | "));
    out.push("The whole lesson as narrated, part by part:\n" + lesson.segments.map((sg, i) => `[${i + 1}] ${parseNarration(sg.narration).spoken}`).join("\n"));
  }
  out.push("The course map (so you can say which lesson covers something):\n" + course.lessons.map((l) => `${l.id} ${l.title}`).join("\n"));
  return out.join("\n\n");
}
// the tutor may only ever open claude.ai: the question carries lesson text and whatever the learner typed
function claudeAddress(v) { try { const u = new URL(v); return u.protocol === "https:" && u.hostname === "claude.ai" ? u.href : ""; } catch { return ""; } }
function openInClaude(lesson, ask, at) {
  const tail = "\n\nMy question: " + Array.from(ask).slice(0, 1800).join("");
  const head = WHO + "\n\n" + moment(lesson, at);
  let q = Array.from(head).slice(0, 5500 - tail.length).join("") + tail;           // trim the context, never the question
  while (encodeURIComponent(q).length > 7000) q = Array.from(q.slice(0, q.length - tail.length)).slice(0, -200).join("") + tail;
  copy(q, "Question copied. Opening Claude");
  const base = claudeAddress(store.setting("claudeUrl")) || "https://claude.ai/new";
  window.open(base + (base.includes("?") ? "&" : "?") + "q=" + encodeURIComponent(q), "_blank", "noopener");
}
// How the tutor is reached right now: "api" (the site calls Claude and the answer streams in), "relay" (Claude Code
// on a machine of the owner's answers), or "link" (neither: the question opens claude.ai).
const relay = {
  mode: null, at: 0,
  get known() { return this.mode == null ? null : this.mode !== "link"; },
  async online(fresh = false) {
    if (!fresh && this.mode != null && Date.now() - this.at < 30000) return this.known;
    try { const r = await fetch("/api/tutor/status", { credentials: "same-origin" }), st = r.ok ? await r.json() : {}; this.mode = st.mode === "api" ? "api" : st.online === true ? "relay" : "link"; }
    catch { this.mode = "link"; }
    this.at = Date.now();
    return this.known;
  },
  /** Ask. `onText(soFar)` is called as the answer grows (API mode); the whole answer is returned at the end. */
  async ask(question, lesson, at, history, onText) {
    const r = await fetch("/api/tutor/ask", { method: "POST", credentials: "same-origin", headers: { "content-type": "application/json" },
      body: JSON.stringify({ question, moment: moment(lesson, at), lesson: lessonText(lesson), history }) });
    if (r.status === 401) { location.href = "/login" + location.hash; throw new Error("You were signed out."); }
    if (r.status === 503) { this.mode = "link"; throw new Error("The tutor went offline just now. Ask again and the question will open in Claude instead."); }
    if (r.status === 429) throw new Error((await r.json().catch(() => ({}))).message || "That is the tutor's limit for now. “Open in Claude” below still works.");
    if (!r.ok) throw new Error("The question could not be sent. Try again.");
    if ((r.headers.get("content-type") || "").includes("ndjson")) return this.readStream(r, onText);
    const { id } = await r.json();
    for (let k = 0; k < 6; k++) {                 // the relay: the server holds each wait open for up to 25 seconds
      const a = await fetch("/api/tutor/answer?id=" + encodeURIComponent(id), { credentials: "same-origin" });
      if (!a.ok) break;
      const body = await a.json();
      if (body.text != null) return body.text;
      if (body.error) throw new Error(body.error);
    }
    throw new Error("No answer came back in time. Try again.");
  },
  /** The API's answer arrives as lines of JSON: pieces of text, then "done", or an error that is safe to show. */
  async readStream(r, onText) {
    const reader = r.body.getReader(), dec = new TextDecoder();
    let buf = "", text = "", finished = false;
    const take = (line) => {
      if (!line.trim()) return;
      let ev; try { ev = JSON.parse(line); } catch { return; }
      if (ev.t === "delta") { text += ev.text; onText?.(text); }
      else if (ev.t === "done") finished = true;
      else if (ev.t === "error") throw new Error(ev.message || "The tutor could not answer just now.");
    };
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i; while ((i = buf.indexOf("\n")) >= 0) { take(buf.slice(0, i)); buf = buf.slice(i + 1); }
    }
    take(buf);
    if (!text.trim()) throw new Error("No answer came back. Try again.");
    if (!finished) text += "\n\n(The answer was cut off. Ask again if it stopped mid-thought.)";
    return text;
  },
};
// One conversation per lesson (or lab), held here and not inside a tutor box: every step of a lesson rebuilds the
// page, and an answer that arrives after the learner has moved on must land in the conversation, not in a box that
// is no longer on screen. Kept in this browser, so a question asked last week is still under its lesson.
const threads = {
  live: new Map(),
  get(key) {
    let t = this.live.get(key);
    if (!t) {
      let turns = [];
      try { const v = JSON.parse(localStorage.getItem("gt.tutor." + key)); if (Array.isArray(v)) turns = v; } catch { /* start empty */ }
      this.live.set(key, (t = { key, turns, busy: false, boxes: new Set() }));
    }
    return t;
  },
  save(t) { try { localStorage.setItem("gt.tutor." + t.key, JSON.stringify(t.turns.filter((x) => !x.failed).slice(-40))); } catch { /* fine */ } },
  /** Redraw every box showing this conversation; forget boxes that have left the page. */
  changed(t) { for (const b of [...t.boxes]) { if (b.el.isConnected) { b.seen = true; b.draw(); } else if (b.seen) t.boxes.delete(b); else b.draw(); } },
};
/** The tutor writes plain text with a little emphasis. Build it from nodes, never from HTML. */
function prose(text) {
  const inline = (line) => line.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g).filter(Boolean).map((part) => (/^\*\*.+\*\*$/.test(part) ? h("b", { text: part.slice(2, -2) }) : /^`.+`$/.test(part) ? h("code", { text: part.slice(1, -1) }) : part));
  const out = []; let list = null, para = [];
  const flush = () => { if (para.length) out.push(h("p", {}, inline(para.join(" ")))); para = []; };
  for (const line of String(text).trim().split("\n")) {
    const item = /^\s*(?:[-*•]|\d+[.)])\s+(.*)$/.exec(line);
    if (item) { flush(); if (!list) out.push((list = h("ul", { class: "list" }))); list.append(h("li", {}, inline(item[1]))); continue; }
    list = null;
    if (!line.trim()) flush(); else para.push(line.replace(/^#+\s*/, "").trim());
  }
  flush();
  return out;
}
/**
 * The tutor box. `where()` describes the moment ({ label, where, detail, seg, t }); `key` names the conversation.
 */
function tutorBox(lesson, where, what = "lesson", key = lesson?.id || what) {
  const DEFAULT = `Explain this ${what}'s main idea a different way, with a fresh example.`;
  const T = threads.get(key);
  const list = h("div", { class: "thread", "aria-live": "polite" });
  const inp = h("input", { type: "text", maxlength: 2000, placeholder: `Ask anything about this ${what}…`, "aria-label": "Question for the tutor", id: "tutor-q-" + key });
  const note = h("p", { class: "note tutor-note", text: "Checking for the tutor…" });
  const clear = btn("Clear this conversation", () => { T.turns.length = 0; threads.save(T); threads.changed(T); }, "small ghost");
  const other = btn("Open in Claude instead", () => openInClaude(lesson, inp.value.trim() || DEFAULT, where?.() || {}), "small ghost");
  const jump = (t) => { if (player && t.seg != null) { player.show(t.seg, false, t.t || 0); player.wrap.scrollIntoView({ behavior: "smooth", block: "nearest" }); } };
  const draw = () => {
    list.replaceChildren(...T.turns.map((t) => (t.role === "me"
      ? h("div", { class: "turn me" }, t.label ? h("button", { class: "at", type: "button", title: lesson && t.seg != null ? "Go back to this moment" : null, disabled: !(player && t.seg != null), text: t.label, onclick: () => jump(t) }) : null, h("p", { text: t.text }))
      : h("div", { class: "turn tutor" + (t.failed ? " failed" : "") }, prose(t.text)))),
      ...(T.busy ? [T.live ? h("div", { class: "turn tutor live" }, prose(T.live)) : h("div", { class: "turn tutor wait" }, h("p", { text: "Thinking…" }))] : []));
    clear.hidden = !T.turns.length || T.busy;
  };
  const say = (on) => {
    other.hidden = !on;                       // when the tutor is not connected, asking already opens Claude
    note.textContent = on ? (relay.mode === "api" ? `Answered here by Claude. It is told where you were in the ${what} when you asked.` : `Answered here by Claude, through the relay on your own machine. It is told where you were in the ${what} when you asked.`)
      : `The tutor is not connected right now, so a question opens Claude in a new tab, with this moment of the ${what} already in the message.`;
  };
  const refresh = (fresh) => relay.online(fresh).then(say);
  const ask = async (q) => {
    q = (q ?? inp.value).trim() || DEFAULT;
    if (T.busy) return;
    const at = where?.() || {};
    // Opening a new tab must happen inside the click itself, or a browser may block it. So when the tutor is
    // already known to be offline, open Claude at once and check again in the background for next time.
    if (relay.known === false) { openInClaude(lesson, q, at); refresh(true); return; }
    if (relay.known == null && !(await relay.online())) { say(false); return openInClaude(lesson, q, at); }
    inp.value = "";
    const history = T.turns.filter((x) => !x.failed).slice(-8).map(({ role, text }) => ({ role, text }));
    T.turns.push({ role: "me", text: q, label: at.label, seg: at.seg, t: at.t, at: Date.now() });
    T.busy = true; threads.save(T); threads.changed(T);            // the question is kept even if the page is left before the answer
    list.lastChild?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    let frame = 0;
    const grow = (soFar) => { T.live = soFar; if (!frame) frame = requestAnimationFrame(() => { frame = 0; threads.changed(T); }); };   // redraw at most once a frame
    try { T.turns.push({ role: "tutor", text: await relay.ask(q, lesson, at, history, grow), at: Date.now() }); }
    catch (e) { T.turns.push({ role: "tutor", failed: true, text: e.message || "No answer came back. Try again." }); refresh(true); }
    T.busy = false; T.live = ""; threads.save(T); threads.changed(T);
  };
  inp.addEventListener("keydown", (e) => { if (e.key === "Enter") ask(); });
  const box = h("div", { class: "section tutor" }, h("h3", { text: T.turns.length ? "Your tutor" : "Stuck? Ask your tutor" }), list,
    h("div", { class: "row" }, h("div", { style: { flex: "1 1 260px", minWidth: 0 } }, inp), btn("Ask", () => ask(), "", "spark")),
    h("div", { class: "row" }, ["Explain it differently", "Give me a harder example", "How would this go wrong on real data?", "Quiz me on this"].map((t) => btn(t, () => ask(t), "small ghost"))),
    h("div", { class: "row" }, note, other, clear));
  T.boxes.add({ el: box, draw, seen: false });
  draw(); refresh();
  box.ask = ask;
  return box;
}

// ---------- multiple-choice question, shared by the lesson quiz and the daily review ----------
function mcq(q, { onAnswer, label }) {
  const order = shuffle(q.options.map((_, i) => i)), wrap = h("div", { class: "q" });
  const why = h("div", { class: "why", role: "status", hidden: true });
  const opts = h("div", { class: "opts", role: "group", "aria-label": "Answers" }, order.map((oi, k) => h("button", { class: "opt", type: "button", onclick: (e) => {
    const right = oi === q.answer;
    opts.querySelectorAll(".opt").forEach((b, j) => { b.disabled = true; if (order[j] === q.answer) b.classList.add("right"); });
    if (!right) e.currentTarget.classList.add("wrong");
    why.hidden = false; why.replaceChildren(h("b", { text: right ? "Right." : `Not quite. The answer is ${"ABCD"[order.indexOf(q.answer)]}.` }), h("span", { text: q.why }));
    onAnswer(right);
  } }, h("i", { text: "ABCD"[k] }), h("span", { text: q.options[oi] }))));
  if (label) wrap.append(h("div", { class: "concept eyebrow", text: label }));
  wrap.append(h("h3", { text: q.q }), opts, why, h("p", { class: "keys", text: "Keys: A to D to answer, Enter to go on" }));
  wrap.pick = (k) => { const b = opts.querySelectorAll(".opt")[k]; if (b && !b.disabled) b.click(); };
  return wrap;
}

// ---------- home ----------
function nextLesson() { return course.lessons.find((l) => !lessonState(l.id).done) || null; }
function home() {
  const st = store.stats(course), nx = nextLesson(), dueN = dueQueue().length;
  const first = !Object.keys(store.state.lessons).length;
  const openPractice = course.practice.some((x) => !store.state[x.kind === "case" ? "cases" : "labs"][x.id]?.done);
  // the review card must say the same thing the Review page will say
  const waiting = store.due().filter((c) => cardQuestion(c)).length, inDeck = Object.keys(store.state.cards).length, nd = store.nextDue();
  const reviewLine = waiting > dueN ? `Today's ${plural(store.reviewedToday(), "card")} done. ${waiting - dueN} more ${waiting - dueN === 1 ? "is" : "are"} waiting and will keep until tomorrow.`
    : inDeck ? (nd ? `Nothing due today. Next cards come back ${nd - Date.now() < 28 * 3600e3 ? "tomorrow" : new Date(nd).toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "short" })}.` : "Nothing due today.")
    : "Review cards appear here after your first lesson.";
  const hero = h("section", { class: "card hero" },
    h("div", { class: "eyebrow", text: first ? "Start here" : nx ? "Next up" : "Course complete" }),
    h("h1", { text: first ? "Machine learning, from the ground up, for the work you already do" : nx ? nx.title : "You have finished every lesson" }),
    h("p", { text: first ? `${course.lessons.length} short lessons, about ${Math.round(course.lessons.reduce((a, l) => a + lessonMin(l), 0) / 60)} hours in all: one a day finishes in about five weeks. You will not be asked to write models by hand: you will learn to frame a question, brief an AI assistant in stages, and audit what comes back. Every number was computed on simulated advertiser data, so the truth is known and nothing is confidential.` : nx ? nx.subtitle : openPractice ? "Keep the daily review going and work through the practice files: that is where it sticks." : "Every lesson and practice file is done. Keep the daily review going, and take the field guide to work." }),
    h("div", { class: "hero-actions" }, nx ? link(first ? "Begin lesson 1" : "Continue", `#/lesson/${nx.id}`, "primary") : openPractice ? link("Practice files", "#/practice", "primary") : link("Open the field guide", "#/guide", "primary"),
      first ? link("How this course was checked", "#/about", "ghost") : null),
    nx ? h("div", { class: "next-meta" }, h("span", { text: `Module ${nx.module} · Lesson ${nx.id.split("-")[1]}` }), h("span", { text: `about ${lessonMin(nx)} min with questions` }), lessonState(nx.id).seg ? h("span", { class: "pill", text: `in progress` }) : null) : null);
  // first visit: say what the parts are, once
  const how = !prefs.get("howto") && st.done < 2 ? h("section", { class: "card howto" },
    h("div", { class: "howto-grid" }, [["01", "Lessons", "Take a guess, watch about five minutes, answer four questions. One idea each."],
      ["02", "Review and drills", "A few cards a day bring each idea back just before you would forget it. Drills do the same by ear."],
      ["03", "Practice", "Audit a report an assistant wrote, or run the work with your own assistant and compare."],
      ["04", "Field guide", "Every brief and audit check you unlock, in one place, ready to paste at work."]].map(([n, t, d]) => h("div", {}, h("span", { class: "idx", text: n }), h("b", { text: t }), h("p", { text: d })))),
    btn("Got it", (e) => { prefs.set("howto", 1); e.currentTarget.closest(".howto").remove(); }, "small ghost")) : null;
  const mods = h("div", { class: "modules" }, course.modules.map((m) => {
    const ls = course.lessons.filter((l) => l.module === m.n), doneN = ls.filter((l) => lessonState(l.id).done).length, extra = course.practice.filter((p) => p.after === m.n);
    const mins = ls.reduce((a, l) => a + lessonMin(l), 0);
    return h("section", { class: "card module" },
      h("div", { class: "module-head" }, h("span", { class: "eyebrow", text: `Module ${m.n} · ${plural(ls.length, "lesson")} · about ${mins} min` }), h("h2", { text: m.title }), h("span", { class: "mbar", title: `${doneN} of ${ls.length} lessons done` }, h("i", { style: { width: `${(100 * doneN) / ls.length}%` } }))),
      ls.map((l) => { const s = lessonState(l.id), cls = s.done ? "done" : l === nx ? "next" : s.seg || s.watched ? "partial" : ""; const d = h("span", { class: "dot" }); if (s.done) d.innerHTML = ICON.check; else d.textContent = l.id.split("-")[1];
        return h("a", { class: "lrow " + cls, href: `#/lesson/${l.id}` }, d, h("span", {}, h("b", { text: l.title }), h("small", { text: l.subtitle })), h("span", { class: "meta", text: `${lessonMin(l)} min` })); }),
      extra.length ? h("div", { class: "sub eyebrow", text: "Practice for this module" }) : null,
      extra.map((p) => practiceRow(p)));
  }));
  const today = st.weekdayToday;
  const aside = h("aside", { class: "home-side" },
    h("section", { class: "card side-card" }, h("div", { class: "progress-row" }, h("div", { class: "pring", style: { "--p": st.pct }, "data-label": st.pct + "%" }), h("div", {}, h("h3", { text: `${st.done} of ${st.total} lessons` }), h("p", { text: `${st.minutes} minutes watched` }))),
      h("div", { class: "stats" }, h("div", { class: "card stat" }, h("b", { text: String(dueN) }), h("span", { text: dueN === 1 ? "card to review today" : "cards to review today" })), h("div", { class: "card stat" }, h("b", { text: String(Object.keys(store.state.cards).length) }), h("span", { text: "ideas under review" }))),
      h("div", {}, h("div", { class: "eyebrow", style: { marginBottom: "8px" }, text: "Days you studied, last 7" }), h("div", { class: "week" }, st.week.map((on, k) => h("span", { class: on ? "on" : "" }, h("i"), "SMTWTFS"[(today - 6 + k + 14) % 7])))),
      dueN ? link(`Review ${plural(dueN, "card")} · about ${Math.max(1, Math.round(dueN / 2))} min`, "#/review", "due") : h("p", { text: reviewLine })),
    h("section", { class: "card side-card" }, h("h3", { text: "Practice" }), h("p", { text: `${plural(course.practice.filter((p) => p.kind === "case").length, "case file")} to audit and ${plural(course.practice.filter((p) => p.kind === "lab").length, "lab")} to run with your own assistant. They unlock nothing: open one whenever you like.` }), link("Open practice", "#/practice", "small")),
    h("section", { class: "card side-card" }, h("h3", { text: "On the move?" }), h("p", { text: "Recall drills are audio-only: a question, a pause to answer in your head, then the answer." }), link("Recall drills", "#/drills", "small")),
    h("section", { class: "card side-card" }, h("h3", { text: "Your field guide" }), h("p", { text: "Every brief and audit check you have unlocked, in one place, and one file to hand your assistant." }), link("Open the field guide", "#/guide", "small")));
  return h("div", { class: "home view" }, h("div", { class: "home-main" }, hero, how, mods), aside);
}

// ---------- lesson ----------
const STEPS = [["guess", "Guess"], ["watch", "Watch"], ["check", "Check"], ["explain", "Explain"], ["take", "Take away"]];
const OPTIONAL = new Set(["explain"]);
const session = {                       // answers to a quiz in progress survive a reload or a look back at the video
  get: (k) => { try { return JSON.parse(sessionStorage.getItem("gt." + k)); } catch { return null; } },
  set: (k, v) => { try { v == null ? sessionStorage.removeItem("gt." + k) : sessionStorage.setItem("gt." + k, JSON.stringify(v)); } catch { /* fine */ } },
};
function lesson(id, stepArg) {
  const les = L(id);
  if (!les) return notFound(/^\d-\d$/.test(id || "") ? `Lesson ${id} is not available right now` : undefined);
  const s = lessonState(id), idx = course.lessons.indexOf(les), nxt = course.lessons[idx + 1], mod = course.modules.find((m) => m.n === les.module);
  let step = stepArg || (s.done ? "take" : s.watched && !s.quiz ? "check" : s.guess != null ? "watch" : "guess");
  const panel = h("div"), tabs = h("ol", { class: "steps" });
  const doneStep = (k) => ({ guess: lessonState(id).guess != null, watch: !!lessonState(id).watched, check: !!lessonState(id).quiz, explain: lessonState(id).recall != null, take: !!lessonState(id).took })[k];
  const goal = h("p", { class: "goal", text: les.goal });
  // four numbered steps; "Explain" is optional and says so, so a finished lesson never looks unfinished
  const drawTabs = () => { let n = 0; tabs.replaceChildren(...STEPS.map(([k, label]) => { const opt = OPTIONAL.has(k), num = opt ? "+" : ++n;
    return h("li", {}, h("button", { type: "button", class: (doneStep(k) ? "done" : "") + (opt ? " optional" : ""), "aria-current": k === step ? "step" : null, title: opt ? "Optional" : null, onclick: () => go(k) },
      (() => { const ic = h("i"); if (doneStep(k)) ic.innerHTML = ICON.check; else ic.textContent = num; return ic; })(), h("span", {}, label, opt ? h("small", { text: " optional" }) : null))); })); };
  // each step is its own address, so the browser's Back button walks Check -> Watch -> Guess -> the course
  const go = (k) => { location.hash = `#/lesson/${id}/${k}`; };
  // a lesson is finished when its four questions are answered; watching is recorded separately
  const settle = () => { const st = lessonState(id); if (!st.done && st.quiz) store.put("lessons", id, { done: Date.now() }); };
  const VIEW = {
    guess() {
      const p = les.predict, reveal = h("div", { class: "why", role: "status", hidden: true }), cont = h("div", { class: "row", hidden: true }, btn("Watch the lesson", () => go("watch"), "primary", "play"));
      const skip = h("div", { class: "row" }, btn("Skip the guess", () => { store.put("lessons", id, { guess: -1 }); go("watch"); }, "ghost small"));
      return h("section", { class: "card panel view" }, h("div", { class: "eyebrow", text: "Before you watch · a wrong guess costs nothing" }), h("h2", { text: p.q }),
        h("div", { class: "opts", style: { maxWidth: "760px" } }, p.options.map((o, i) => h("button", { class: "opt", type: "button", onclick: (e) => {
          e.currentTarget.parentNode.querySelectorAll(".opt").forEach((b, j) => { b.disabled = true; if (j === p.answer) b.classList.add("right"); });
          if (i !== p.answer) e.currentTarget.classList.add("wrong");
          reveal.hidden = false; reveal.replaceChildren(h("b", { text: i === p.answer ? "Good instinct." : "A common guess." }), h("span", { text: p.reveal })); cont.hidden = false; skip.hidden = true;
          store.put("lessons", id, { guess: i }); drawTabs(); cont.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } }, h("i", { text: "ABCD"[i] }), h("span", { text: o })))), reveal, cont, skip);
    },
    watch() {
      const mount = h("div"), tr = h("div", { class: "transcript", hidden: true });
      const segs = les.segments.map((sg, i) => ({ ...sg, src: les.audio?.[i]?.src, dur: les.audio?.[i]?.dur, label: sg.visual.title || les.title }));
      const mark = (i) => tr.querySelectorAll("button").forEach((el, k) => el.classList.toggle("cur", k === i));
      player = new Player(mount, { segments: segs, title: les.title, startAt: lessonState(id).watched ? 0 : lessonState(id).seg || 0, ctx, prefs,
        // opening the page is not "moving": only write the position when the learner (or playback) actually changes part
        onSegment: (i, initial) => { if (!initial) store.put("lessons", id, { seg: i }, { quiet: true, lazy: true }); mark(i); },
        onComplete: () => { store.put("lessons", id, { watched: Date.now(), seg: 0 }); drawTabs(); doneBar.hidden = false; doneBar.scrollIntoView({ behavior: "smooth", block: "nearest" }); } });
      player.onPlay = () => audioCard.current?.pause();
      les.segments.forEach((sg, i) => tr.append(h("button", { type: "button", text: parseNarration(sg.narration).spoken, onclick: () => player.show(i, true) })));
      const doneBar = h("div", { class: "done-banner", hidden: !lessonState(id).watched }, h("h2", { text: "That is the lesson." }),
        h("p", { text: lessonState(id).quiz ? "You have already answered its questions." : "Four questions while it is fresh. This is the part that makes it stick." }),
        lessonState(id).quiz ? btn("See the take-aways", () => go("take"), "primary") : btn("Check yourself", () => go("check"), "primary"));
      return h("div", { class: "view", style: { display: "grid", gap: "16px" } }, mount, doneBar,
        h("section", { class: "card panel" }, h("div", { class: "row" }, btn("Show the transcript", (e) => { tr.hidden = !tr.hidden; e.currentTarget.lastChild.textContent = tr.hidden ? "Show the transcript" : "Hide the transcript"; }, "small"),
          h("span", { style: { color: "var(--ink-3)", fontSize: ".85rem" }, text: "Best watched the first time. The headphones button switches to audio only, for a second pass on the move." })), tr,
          tutorBox(les, () => watchMoment(les))));
    },
    check() {
      const qs = les.quiz, host = h("div"), bar = h("div", { class: "qbar" }, qs.map(() => h("i")));
      const saved = session.get("quiz." + id), res = Array.isArray(saved) ? saved.slice(0, qs.length) : [];
      let i = res.length;
      const show = () => {
        bar.childNodes.forEach((el, k) => (el.className = k < i ? (res[k] ? "ok" : "no") : k === i ? "cur" : ""));
        if (i >= qs.length) return finish();
        const next = h("div", { class: "row end", hidden: true }, btn(i === qs.length - 1 ? "Finish" : "Next question", () => { i++; show(); }, "primary"));
        // no scrolling on answer: the marked options must stay in view with the explanation
        host.replaceChildren(mcq(qs[i], { label: `Question ${i + 1} of ${qs.length}${qs[i].domain === "other" ? " · a different problem, same idea" : ""}`, onAnswer: (ok) => { res[i] = ok; session.set("quiz." + id, res); next.hidden = false; next.firstChild.focus({ preventScroll: true }); } }), next);
      };
      const finish = () => {
        const score = res.filter(Boolean).length;
        session.set("quiz." + id, null);
        les.review.forEach((_, k) => store.seed(`${id}-c${k}`));
        if (id === "1-2") course.triage.forEach((_, k) => store.seed("t-" + k));     // "which kind of problem is this?" cards join the mix
        store.put("lessons", id, { quiz: { score, of: qs.length, t: Date.now() } });
        settle();
        drawTabs();
        const missed = qs.filter((_, k) => !res[k]);
        host.replaceChildren(h("div", { class: "done-banner" }, h("h2", { text: score === qs.length ? "All four. Solid." : `${score} of ${qs.length}.` }),
          h("p", { text: score === qs.length ? "Two ideas from this lesson will come back in your daily review, in a new setting each time." : "The ideas you missed will come back in your daily review, in a new setting each time. That is by design." }),
          missed.length ? h("ul", { class: "missed" }, missed.map((q) => h("li", {}, h("b", { text: q.concept ? q.concept[0].toUpperCase() + q.concept.slice(1) : "Missed" }), h("span", { text: q.why })))) : null,
          h("div", { class: "row" }, btn("See the take-aways", () => go("take"), "primary"), btn("Explain it back first (optional, 30 seconds)", () => go("explain")),
            missed.length ? btn("Try the questions again", () => { session.set("quiz." + id, null); panel.replaceChildren(VIEW.check()); }, "ghost") : null)));
      };
      show();
      const here = () => {
        const q = qs[i];
        if (!q) return { label: "After the check", where: `on the lesson's check, all ${qs.length} questions answered (${res.filter(Boolean).length} right).`, detail: "The questions I got wrong:\n" + (qs.filter((_, k) => !res[k]).map((x) => `- ${x.q} (the course's explanation: ${x.why})`).join("\n") || "none") };
        const answered = res[i] !== undefined;
        return { label: `Check · question ${i + 1}`, where: `on the lesson's check, question ${i + 1} of ${qs.length}.`,
          detail: `The question on screen: ${q.q}\nIts options (shown to me in a shuffled order, so refer to them by their words, not by letter):\n${q.options.map((o) => "- " + o).join("\n")}\n` +
            (answered ? `I answered it ${res[i] ? "correctly" : "wrongly"}. The right option is: "${q.options[q.answer]}". The course's explanation: ${q.why}` : "I have NOT answered it yet. Help me reason towards it; do not tell me which option is right.") };
      };
      return h("section", { class: "card panel view" }, h("div", { class: "task" }, bar, host), tutorBox(les, here, "question"));
    },
    explain() {
      const r = les.recall, ta = h("textarea", { id: "recall-" + id, placeholder: "Type it, or say it out loud and type nothing." }), model = h("div", { class: "why", role: "status", hidden: true }, h("b", { text: "A strong answer" }), h("span", { text: r.model_answer }));
      const rate = h("div", { class: "section", hidden: true }, h("h3", { text: "Rate yourself to continue" }), h("div", { class: "row" }, [["Missed it", 0], ["Partly", 1], ["Nailed it", 2]].map(([t, v]) => btn(t, () => { store.put("lessons", id, { recall: v }); go("take"); })),
        btn("Have the tutor grade it", () => box.ask("Grade my answer against the model answer on three points: correct, complete, clear. Be specific about what I missed."), "small ghost", "spark")));
      const box = tutorBox(les, () => ({ label: "Explain it back", where: "on the lesson's optional \"explain it back\" step.", detail: `The question I was asked to explain: ${r.prompt}\nThe course's model answer: ${r.model_answer}\nWhat I typed: ${ta.value.trim() || "(nothing: I answered out loud, so ask me to type it)"}` }), "answer");
      const first = h("div", { class: "row" }, btn("Show a strong answer", () => { model.hidden = false; rate.hidden = false; first.hidden = true; }, "primary"), btn("Skip", () => go("take"), "ghost"));
      return h("section", { class: "card panel view" }, h("div", { class: "eyebrow", text: "Optional · explaining it is the fastest way to find the gap" }), h("h2", { text: r.prompt }), h("div", { style: { maxWidth: "760px", display: "grid", gap: "14px" } }, ta, first, model, rate), box);
    },
    take() {
      if (!lessonState(id).took) store.put("lessons", id, { took: Date.now() }, { quiet: true });
      const lastOfModule = !nxt || nxt.module !== les.module, ms = store.state.missions[mod.n] || {};
      const openPractice = course.practice.some((x) => !store.state[x.kind === "case" ? "cases" : "labs"][x.id]?.done);
      return h("div", { class: "view", style: { display: "grid", gap: "16px" } },
        h("section", { class: "card panel" }, h("h2", { text: "Keep these three" }), h("ol", { class: "bul", style: { fontSize: "1rem" } }, les.takeaways.map((t) => h("li", {}, h("span", { text: t })))),
          h("div", { class: "row" }, nxt ? link(`Next: ${nxt.title}`, `#/lesson/${nxt.id}`, "primary") : openPractice ? link("That was the last lesson: on to the practice files", "#/practice", "primary") : link("That was the last lesson: open your field guide", "#/guide", "primary"), link("Course map", "#/", "ghost"))),
        h("div", { class: "cols" },
          h("section", { class: "card panel" }, h("div", { class: "section" }, h("h3", { text: "Ask your assistant" }), copyBox(les.ask_assistant)),
            h("div", { class: "section" }, h("h3", { text: "Before you believe what comes back" }), h("ul", { class: "list" }, les.audit_checklist.map((t) => h("li", { text: t })))),
            lastOfModule ? h("div", { class: "section" }, h("h3", { text: `Module ${mod.n} mission` }), h("p", { style: { color: "var(--ink-2)" }, text: mod.mission }),
              h("label", { class: "check" }, h("input", { type: "checkbox", id: "mission-" + mod.n, checked: !!ms.done, onchange: (e) => store.put("missions", mod.n, { done: e.target.checked }) }), h("span", { text: "Done at work" }))) : null),
          h("section", { class: "card panel" }, h("div", { class: "section" }, h("h3", { text: "Where else this applies" }), h("ul", { class: "list" }, les.transfer.map((t) => h("li", { text: t })))),
            h("div", { class: "section" }, h("h3", { text: "Other ways to attack it" }), h("div", { class: "kv" }, les.other_ways.map((o) => h("div", {}, h("b", { text: o.approach }), h("span", { text: o.when }))))))),
        h("section", { class: "card panel" }, h("h3", { text: "New words, and what the textbooks call them" }), h("div", { class: "kv two" }, les.glossary.map((g) => h("div", {}, h("b", { text: g.term }), h("span", { text: g.def }))))),
        h("section", { class: "card panel" }, tutorBox(les, () => ({ label: "Take-aways", where: "on the lesson's take-away page, after finishing it.", detail: `The brief the lesson suggests I give my assistant: ${les.ask_assistant}\n\nWhat its output must show before I believe it:\n- ${les.audit_checklist.join("\n- ")}` }))));
    },
  };
  if (!Object.hasOwn(VIEW, step)) step = "guess";
  if (!stepArg) history.replaceState(null, "", `#/lesson/${id}/${step}`);
  goal.hidden = !(step === "guess" || step === "take");
  const root = h("div", { class: "view lesson", "data-step": step }, h("header", { class: "lesson-head" }, h("div", { class: "crumbs" }, h("a", { href: "#/", text: "Course" }), h("span", { text: "›" }), h("span", { text: `Module ${mod.n}: ${mod.title}` }), h("span", { text: "›" }), h("span", { text: `Lesson ${les.id.split("-")[1]}` })),
    h("div", { class: "lesson-top" }, h("h1", { text: les.title }), h("nav", { "aria-label": "Lesson steps" }, tabs)), goal), panel);
  panel.replaceChildren(VIEW[step]());       // the view first: opening "Take away" is what ticks it
  drawTabs();
  return root;
}

// ---------- daily review: two ideas per lesson, a different setting each time ----------
function cardQuestion(cid) {
  if (typeof cid !== "string" || !/^(t-\d+|\d+-\d+-c\d+)$/.test(cid)) return null;
  if (cid.startsWith("t-")) { const q = course.triage[+cid.slice(2)]; return q && { q, label: "Which kind of problem?", lesson: null }; }
  const [a, b, c] = cid.split("-"), les = L(`${a}-${b}`), con = les?.review[+c.slice(1)];
  if (!con) return null;
  return { q: con.variants[(store.state.cards[cid]?.n || 0) % con.variants.length], label: `${les.title} · ${con.concept}`, lesson: les };
}
function dueQueue() {
  const cap = Math.max(0, (store.setting("dailyCap") || 10) - store.reviewedToday());
  return store.due().filter((c) => cardQuestion(c)).slice(0, cap);
}
function review() {
  const queue = shuffle(dueQueue()), host = h("div"), res = [];
  let i = 0;
  if (!queue.length) {
    const nd = store.nextDue(), capped = store.due().some((c) => cardQuestion(c));
    return h("section", { class: "card empty view" }, icon("done"), h("h2", { text: capped ? "That is today's review done" : "Nothing due today" }),
      h("p", { text: capped ? "You have hit today's cap. The rest will still be there tomorrow: spacing them out is the point." : nd ? `Next cards are due ${new Date(nd).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" })}.` : "Finish a lesson's questions and its two key ideas will start coming back here." }), link("Back to the course", "#/", "primary"));
  }
  const bar = h("div", { class: "qbar" }, queue.map(() => h("i")));
  const show = () => {
    bar.childNodes.forEach((b, k) => (b.className = k < i ? (res[k] ? "ok" : "no") : k === i ? "cur" : ""));
    if (i >= queue.length) return host.replaceChildren(h("div", { class: "done-banner" }, h("h2", { text: `${res.filter(Boolean).length} of ${queue.length} right` }), h("p", { text: "Right answers come back later; missed ones come back tomorrow, in a different setting." }), link("Back to the course", "#/", "primary")));
    const cid = queue[i], c = cardQuestion(cid);
    const next = h("div", { class: "row end", hidden: true }, c.lesson ? link("Rewatch the lesson", `#/lesson/${c.lesson.id}/watch`, "ghost small") : null, btn(i === queue.length - 1 ? "Finish" : "Next", () => { i++; show(); }, "primary"));
    host.replaceChildren(mcq(c.q, { label: c.label, onAnswer: (ok) => { res[i] = ok; store.answer(cid, ok); drawBadge(); next.hidden = false; next.lastChild.focus({ preventScroll: true }); } }), next);
  };
  show();
  return h("div", { class: "view narrow" }, h("header", { class: "lesson-head" }, h("h1", { text: "Today's review" }), h("p", { text: `${plural(queue.length, "card")}, about ${plural(Math.max(1, Math.round(queue.length / 2)), "minute")}. Mixed across lessons on purpose.` })), h("section", { class: "card panel" }, h("div", { class: "task" }, bar, host)));
}

// ---------- practice: case files and labs ----------
function practiceList() {
  const row = (p) => practiceRow(p, `after module ${p.after} · ${PRACTICE_MIN[p.kind]} min`);
  return h("div", { class: "view narrow wide" }, h("header", { class: "lesson-head" }, h("h1", { text: "Practice" }), h("p", { text: "Lessons explain. These make you do the job: audit a report an assistant wrote, or run the work yourself and compare with known results." })),
    h("section", { class: "card panel two-reports" }, h("div", { class: "eyebrow", text: "Start here · 5 minutes" }), h("h2", { text: "Two reports, one model" }),
      h("p", { class: "lead", text: "The same churn model, written up twice by an assistant. One is handsome and cannot answer a single question. The other is plain and already has. Open both, decide which you would put your name on, then check what you spotted." }),
      h("div", { class: "row" }, h("a", { class: "btn", href: "reports/handsome.html", target: "_blank", rel: "noopener" }, "Open the handsome report"), h("a", { class: "btn", href: "reports/plain.html", target: "_blank", rel: "noopener" }, "Open the plain report")),
      (() => { const d = h("details", {}, h("summary", {}, h("span", { text: "What separates them" }))); d.addEventListener("toggle", async () => { if (d.dataset.done) return; d.dataset.done = 1;
        try { const n = await (await fetch("reports/notes.json")).json(); d.append(h("div", { class: "cols", style: { paddingBottom: "8px" } }, h("div", { class: "section" }, h("h3", { text: "The handsome one" }), h("ul", { class: "list" }, n.handsome.map((t) => h("li", { text: t })))), h("div", { class: "section" }, h("h3", { text: "The plain one" }), h("ul", { class: "list" }, n.plain.map((t) => h("li", { text: t })))))); } catch { d.append(h("p", { class: "lead", text: "The notes could not be loaded." })); } }); return d; })()),
    h("section", { class: "card module" }, h("div", { class: "module-head" }, h("h2", { text: "Case files" }), h("span", { class: "eyebrow", text: "An assistant's report lands on your desk. Would you ship it?" })), course.practice.filter((p) => p.kind === "case").map(row)),
    h("section", { class: "card module" }, h("div", { class: "module-head" }, h("h2", { text: "Labs" }), h("span", { class: "eyebrow", text: "Run it with your own assistant on the practice data, then compare with the course's results" })), course.practice.filter((p) => p.kind === "lab").map(row)));
}
function reportBlock(b) {
  if (b.type === "h") return h("h4", { text: b.text });
  if (b.type === "p") return h("p", { text: b.text });
  if (b.type === "code") return h("pre", { class: "codeblk", text: b.text });
  if (b.type === "kpi") return h("div", { class: "kpis", style: { gridTemplateColumns: `repeat(${Math.min(4, b.items.length)}, minmax(0, 1fr))` } }, b.items.map((x) => h("div", {}, h("b", { text: x.value }), h("span", { text: x.label }))));
  if (b.type === "table") return h("div", { class: "tbl-wrap" }, h("table", { class: "tbl" }, h("thead", {}, h("tr", {}, b.columns.map((c) => h("th", { text: c })))), h("tbody", {}, b.rows.map((r) => h("tr", {}, r.map((c) => h("td", { text: c })))))));
  return null;
}
function caseFile(id) {
  const c = course.practice.find((p) => p.kind === "case" && p.id === id);
  if (!c) return notFound();
  const out = h("div", { class: "section", hidden: true });
  const boxes = c.findings.map((f, i) => h("label", { class: "check" }, h("input", { type: "checkbox", id: `cf-${id}-${i}` }), h("span", { text: f.text })));
  const blocks = c.report.map((b) => h("div", { class: "blk" }, reportBlock(b)));      // a wrapper, so a mark is never clipped by a scrolling table or code block
  const judge = () => {
    const picked = boxes.map((b) => b.firstChild.checked), right = c.findings.filter((f, i) => picked[i] === f.real).length;
    // redline: number each real problem and mark the place in the report that shows it
    const order = c.findings.map((f, i) => [f.real ? Math.min(...(f.marks?.length ? f.marks : [999])) : Infinity, i]).filter(([k]) => k !== Infinity).sort((x, y) => x[0] - y[0] || x[1] - y[1]);
    const num = c.findings.map(() => 0);
    order.forEach(([, i], k) => (num[i] = k + 1));          // numbered top to bottom, the way the report is read
    blocks.forEach((b) => { if (b) { b.classList.remove("marked"); delete b.dataset.mark; b.onclick = null; } });
    c.findings.forEach((f, i) => (f.marks || []).forEach((k) => { const b = blocks[k]; if (b) { b.classList.add("marked"); b.dataset.mark = b.dataset.mark ? `${b.dataset.mark} · ${num[i]}` : String(num[i]);
      b.onclick = () => document.getElementById(`why-${id}-${i}`)?.scrollIntoView({ behavior: "smooth", block: "center" }); } }));
    boxes.forEach((b) => (b.firstChild.disabled = true));
    out.hidden = false;
    out.id = "audit-result";
    out.replaceChildren(h("h3", { text: `${right} of ${c.findings.length} judged correctly` }), h("p", { class: "lead", text: "Each real problem is numbered here and marked in red on the report above. Click a number to jump between the two." }),
      h("div", { class: "kv" }, c.findings.map((f, i) => h("div", { class: picked[i] === f.real ? "" : "missed", id: `why-${id}-${i}` }, h("b", {}, f.real ? h("button", { class: "redline", type: "button", title: "Show it on the report", text: num[i], onclick: () => blocks[(f.marks || [])[0]]?.scrollIntoView({ behavior: "smooth", block: "center" }) }) : null, `${f.real ? "Real problem" : "Not a problem"}${picked[i] === f.real ? "" : " (you had this the other way)"}`), h("span", { class: "said", text: f.text }), h("span", { text: f.why })))),
      h("div", { class: "why" }, h("b", { text: "Verdict" }), h("span", { text: c.verdict })), h("div", { class: "row" }, link("More practice", "#/practice", "primary"), link("Course map", "#/", "ghost")));
    store.put("cases", id, { done: Date.now(), right, of: c.findings.length });
    out.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  return h("div", { class: "view narrow wide" }, h("header", { class: "lesson-head" }, h("div", { class: "crumbs" }, h("a", { href: "#/practice", text: "Practice" }), h("span", { text: "›" }), h("span", { text: "Case file" })), h("h1", { text: c.title }), h("p", { text: c.setup })),
    h("div", { class: "report" }, h("div", { class: "bar" }, h("i"), h("i"), h("i"), h("span", { text: c.file }), h("em", { text: "written by your assistant · not checked by anyone" })), h("div", { class: "body" }, blocks)),
    h("section", { class: "card panel" }, h("div", { class: "eyebrow", text: "Your audit" }), h("h2", { text: c.ask }), h("p", { class: "lead", text: "Tick every item that is a real problem. Some are not: knowing what is fine matters as much." }), h("div", {}, boxes), h("div", { class: "row" }, btn("Check my audit", judge, "primary")), out));
}
function lab(id) {
  const c = course.practice.find((p) => p.kind === "lab" && p.id === id);
  if (!c) return notFound();
  const st = store.state.labs[id] || {};
  return h("div", { class: "view narrow wide" }, h("header", { class: "lesson-head" }, h("div", { class: "crumbs" }, h("a", { href: "#/practice", text: "Practice" }), h("span", { text: "›" }), h("span", { text: "Lab" })), h("h1", { text: c.title }), h("p", { text: c.setup })),
    h("section", { class: "card panel" }, h("h2", { text: "Files" }), h("div", { class: "row" }, c.files.map((f) => h("a", { class: "btn small", href: f.href, download: "" }, f.name))), h("p", { class: "lead", text: "Simulated data: safe to give to any assistant. Never paste real client data into a tool that is not approved for it." })),
    c.steps.map((s, i) => h("section", { class: "card panel" }, h("div", { class: "eyebrow", text: `Stage ${i + 1} of ${c.steps.length}` }), h("h2", { text: s.title }), h("div", { class: "section" }, h("h3", { text: "Say this to your assistant" }), copyBox(s.brief)),
      h("div", { class: "cols" }, h("div", { class: "section" }, h("h3", { text: "You should see roughly" }), h("ul", { class: "list" }, s.expect.map((t) => h("li", { text: t })))), h("div", { class: "section" }, h("h3", { text: "The gate: do not go on until" }), h("ul", { class: "list" }, s.gate.map((t) => h("li", { text: t }))))))),
    h("section", { class: "card panel" }, h("label", { class: "check" }, h("input", { type: "checkbox", id: "lab-" + id, checked: !!st.done, onchange: (e) => store.put("labs", id, { done: e.target.checked ? Date.now() : 0 }) }), h("span", { text: "I ran this and my numbers were in the right neighbourhood" })),
      tutorBox(null, () => ({ label: "Lab", where: `working through a practice lab called "${c.title}".`, detail: `${c.setup}\n\nIts stages:\n${c.steps.map((x, k) => `${k + 1}. ${x.title}. Brief: ${cut(x.brief, 500)} Gate: ${x.gate.join("; ")}`).join("\n")}` }), "lab", "lab-" + id)));
}

// ---------- recall drills (audio only) ----------
function drills() {
  return h("div", { class: "view narrow" }, h("header", { class: "lesson-head" }, h("h1", { text: "Recall drills" }), h("p", { text: "Eyes-free practice for a walk or a commute. You hear a question, get a few seconds to answer in your head, then hear the answer. One drill per module, two questions from each of its lessons; it opens when you finish the module." })),
    course.modules.map((m) => {
      const ls = course.lessons.filter((l) => l.module === m.n), doneN = ls.filter((l) => lessonState(l.id).done).length, d = course.drills?.[m.n], open = doneN === ls.length;
      return h("section", { class: "card panel" }, h("div", { class: "eyebrow", text: `Module ${m.n}` }), h("h2", { text: m.title }),
        d?.src ? (open ? audioCard(d.src, d.dur, `the module ${m.n} drill`) : h("p", { class: "lead", text: `${doneN} of ${ls.length} lessons done. The drill opens when you finish the module.` })) : h("p", { class: "lead", text: "Audio for this drill is not generated yet." }),
        d?.src && open ? h("p", { class: "lead small", text: `${d.items.length} questions · ${Math.round(d.dur / 60)} min` }) : null,
        d && open ? h("details", {}, h("summary", {}, h("span", { text: `Read the ${d.items.length} questions` })), h("div", { class: "kv", style: { marginTop: "10px" } }, d.items.map((x) => h("div", {}, h("b", { text: x.q }), h("span", { text: x.a }))))) : null);
    }));
}

// ---------- field guide ----------
function guide() {
  const search = h("input", { type: "text", id: "gloss-q", placeholder: "Search the glossary…", "aria-label": "Search the glossary" }), list = h("div", { class: "gloss-grid" });
  const drawGloss = () => { const q = search.value.trim().toLowerCase(), hits = course.glossary.filter((g) => !q || (g.term + " " + g.def).toLowerCase().includes(q));
    if (!hits.length) return list.replaceChildren(h("p", { class: "lead", text: `No term matches "${search.value.trim()}". The tutor button on any lesson will explain it.` }));
    list.replaceChildren(...hits.map((g) => h("div", { class: "gloss" }, h("b", { text: g.term }), h("span", { text: g.def }), h("a", { href: `#/lesson/${g.lesson}`, text: `Lesson ${g.lesson}` })))); };
  search.addEventListener("input", drawGloss); drawGloss();
  const unlocked = course.lessons.filter((l) => lessonState(l.id).done);
  return h("div", { class: "view narrow wide" }, h("header", { class: "lesson-head" }, h("h1", { text: "Field guide" }), h("p", { text: "What to say to your assistant, and what its output has to show before you believe it. It grows as you finish lessons." })),
    h("section", { class: "card panel" }, h("h2", { text: "The path, for any question" }), h("ol", { class: "bul", style: { fontSize: "1rem" } }, course.path.map((t) => h("li", {}, h("span", { text: t })))),
      h("div", { class: "row" }, h("a", { class: "btn primary", href: "data/assistant-core.md", download: "" }, "Download the one-page instructions"), h("a", { class: "btn", href: "data/assistant-pack.md", download: "" }, "Full reference, all lessons")),
      h("p", { class: "lead small", text: "The one-pager is the standing instruction to pin in your assistant: how we work, and the path for any question. The full reference adds every lesson's brief and checks; it is complete from day one, so expect parts you have not studied yet." })),
    h("section", { class: "card panel" }, h("h2", { text: `Briefs and checks you have unlocked (${unlocked.length} of ${course.lessons.length})` }), unlocked.length ? [...unlocked.map((l) => h("details", { class: "bm" }, h("summary", {}, h("span", { class: "idx", text: `Lesson ${l.id}` }), h("b", { text: l.title })), h("div", { style: { display: "grid", gap: "12px", padding: "4px 0 18px" } }, h("div", { class: "eyebrow", text: "Say this to your assistant" }), copyBox(l.ask_assistant), h("div", { class: "eyebrow", text: "Before you believe what comes back" }), h("ul", { class: "list" }, l.audit_checklist.map((t) => h("li", { text: t })))))),
        unlocked.length < course.lessons.length ? h("p", { class: "lead small", text: `${course.lessons.length - unlocked.length} more unlock as you finish lessons.` }) : null] : h("p", { class: "lead", text: "Finish your first lesson and its brief and audit checks land here." })),
    h("section", { class: "card panel" }, h("h2", { text: `Glossary (${course.glossary.length} terms)` }), search, list));
}

// ---------- about, settings ----------
// Erasing everything is a different, deliberate act from pressing a button twice: type the word, and it can still be undone.
function eraseControls() {
  const word = h("input", { type: "text", "aria-label": "Type ERASE to confirm", placeholder: "Type ERASE", autocomplete: "off", style: { maxWidth: "200px" } });
  const undoBox = h("div", { class: "section", hidden: !store.syncStatus().undoAt }, h("p", { text: "You started over recently. The copy from just before is kept for a week, and bringing it back keeps whatever you have done since." }),
    h("div", { class: "row" }, btn("Bring my progress back", async () => { toast((await store.restore()) ? "Progress restored" : "Nothing to restore"); route(); }, "small")));
  const confirmBox = h("div", { class: "confirm", hidden: true }, h("b", { text: "Erase all progress on every device?" }),
    h("p", { text: "Finished lessons, review cards and practice ticks are cleared. Settings are kept. You can undo this from here afterwards." }),
    h("div", { class: "row" }, word, btn("Erase everything", async () => { if (word.value.trim().toUpperCase() !== "ERASE") return toast("Type ERASE to confirm"); await store.resetAll(); toast("Progress cleared"); route(); }, "small"),
      btn("Cancel", () => { confirmBox.hidden = true; word.value = ""; }, "small ghost")));
  let shown = false;
  const off = store.onChange(() => { if (undoBox.isConnected) shown = true; else if (shown) return off(); undoBox.hidden = !store.syncStatus().undoAt; });
  return { confirmBox, undoBox };
}
function about(toSettings) {
  const { confirmBox, undoBox } = eraseControls();
  if (toSettings) setTimeout(() => document.getElementById("settings")?.scrollIntoView({ block: "start" }), 60);
  return h("div", { class: "view prose narrow" }, h("header", { class: "lesson-head" }, h("h1", { text: "How this course was built and checked" })),
    course.colophon ? h("dl", { class: "colophon" }, course.colophon.map(([k, v]) => h("div", {}, h("dt", { text: k }), h("dd", { text: v })))) : null,
    course.about.flatMap((s) => [h("h2", { text: s.h }), ...s.p.map((t) => h("p", { text: t }))]),
    h("section", { class: "card panel", id: "settings", style: { color: "var(--ink)" } }, h("h2", { text: "Settings" }),
      h("div", { class: "section" }, h("h3", { text: "Daily review cap" }), h("div", { class: "seg-btns" }, [6, 10, 16].map((n) => h("button", { type: "button", text: `${n} cards`, "aria-pressed": String((store.setting("dailyCap") || 10) === n), onclick: (e) => { store.setting("dailyCap", n); e.currentTarget.parentNode.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === e.currentTarget))); drawBadge(); } })))),
      h("div", { class: "section" }, h("h3", { text: "The tutor" }), h("p", { text: "Questions are answered on the lesson page by Claude, which is told the exact moment of the lesson you asked from. That needs either the site's own Claude API key (paid from the API credit included in a Max plan) or the tutor relay running on a computer of yours. With neither, a question opens Claude in a new tab instead. This box sets where that tab goes: leave it empty for a new chat, or paste the address of a Claude Project that holds the assistant pack to keep one running conversation." }),
        h("input", { type: "url", id: "claude-url", placeholder: "https://claude.ai/project/…", value: store.setting("claudeUrl") || "", onchange: (e) => { const v = e.target.value.trim(); if (v && !claudeAddress(v)) { toast("That is not a claude.ai address"); e.target.value = store.setting("claudeUrl") || ""; return; } store.setting("claudeUrl", v); toast("Saved"); } })),
      h("div", { class: "section" }, h("h3", { text: "Your progress" }), h("div", { class: "row" }, btn("Download a copy", () => { const a = h("a", { href: URL.createObjectURL(new Blob([store.exportState()], { type: "application/json" })), download: "ground-truth-progress.json" }); a.click(); }, "small"),
        btn("Start over…", () => { confirmBox.hidden = false; confirmBox.querySelector("input").focus(); }, "small ghost"), h("form", { method: "post", action: "/logout", style: { display: "inline" } }, h("button", { class: "btn small ghost", type: "submit", text: "Sign out" }))),
        confirmBox, undoBox)));
}
const notFound = (msg) => h("section", { class: "card empty view" }, h("h2", { text: msg || "That page does not exist" }), nextLesson() ? link(`Go to ${nextLesson().title}`, `#/lesson/${nextLesson().id}`, "primary") : null, link("Back to the course", "#/", nextLesson() ? "" : "primary"));

// ---------- router ----------
const ROUTES = { "": home, lesson, review, practice: practiceList, case: caseFile, lab, drills, guide, about: () => about(false), settings: () => about(true) };
function drawBadge() { const n = dueQueue().length, bd = $("#due-badge"); bd.hidden = !n; bd.textContent = n; }
function route() {
  player?.destroy(); player = null;
  audioCard.current?.pause();                                  // a drill must not keep talking under another page
  const [, name = "", a, b] = (location.hash || "#/").split("/");
  let view;
  try { view = (Object.hasOwn(ROUTES, name) ? ROUTES[name] : notFound)(a, b); } catch (e) { console.error(e); view = notFound("That page could not be shown"); }
  main.replaceChildren(view);
  document.querySelectorAll(".nav a").forEach((el) => el.setAttribute("aria-current", el.dataset.r === (name === "case" || name === "lab" ? "practice" : name === "settings" ? "about" : name) ? "page" : "false"));
  drawBadge();
  document.title = name === "lesson" && L(a) ? `${L(a).title} · Ground Truth` : "Ground Truth";
  if (name !== "settings") scrollTo({ top: 0 });
  const h1 = view.querySelector?.("h1");                       // tell a screen reader the page changed
  if (h1 && routed) { h1.tabIndex = -1; h1.focus({ preventScroll: true }); }
  routed = true;
}
let routed = false;
function syncBadge() {
  const m = store.syncStatus().mode, el = $("#sync");
  el.classList.toggle("off", m !== "synced");
  el.lastChild.textContent = { synced: "Synced", saving: "Saving…", local: "Saved on this device" }[m];
  el.title = m === "local" ? "Could not reach the server; your progress is safe in this browser and will sync when it can." : m === "saving" ? "Sending your latest progress." : "Progress is saved to your account.";
}

addEventListener("keydown", (e) => {
  if (!(e.target instanceof Element) || e.repeat || e.target.closest("input, textarea, select") || e.metaKey || e.ctrlKey || e.altKey) return;
  const q = document.querySelector(".q");
  if (!q) return;
  const k = "abcd".indexOf(e.key.toLowerCase()), n = "1234".indexOf(e.key);
  if ((k >= 0 || n >= 0) && q.pick) { q.pick(k >= 0 ? k : n); e.preventDefault(); }
});

window.__gt = { get player() { return player; }, get course() { return course; }, store };     // a handle for testing from the console

(async function boot() {
  const theme = prefs.get("theme"); if (theme) document.documentElement.dataset.theme = theme;
  $("#theme").addEventListener("click", () => { const dark = (document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark"; document.documentElement.dataset.theme = dark ? "light" : "dark"; prefs.set("theme", dark ? "light" : "dark"); });
  try {
    const r = await fetch("data/course.json");
    if (r.redirected && new URL(r.url).pathname.startsWith("/login")) return void (location.href = "/login" + location.hash);
    course = await r.json();
  } catch { main.replaceChildren(h("section", { class: "card empty" }, h("h2", { text: "The course could not be loaded" }), h("p", { text: "Check your connection and reload. If you were signed out, reloading takes you to the sign-in page." }))); return; }
  // show the page from what this browser already knows, then fetch the server's copy: the first screen never waits on it
  store.initLocal();
  store.onChange(() => { syncBadge(); drawBadge(); }); syncBadge();
  addEventListener("hashchange", route);
  route();
  const quiet = () => ["", "practice", "guide", "drills"].includes((location.hash || "#/").split("/")[1] || "");
  store.sync().then((changed) => { if (changed && quiet()) route(); });   // never redraw under a lesson or a review in progress
})();
