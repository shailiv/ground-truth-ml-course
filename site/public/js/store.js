// Progress: kept in this browser at once, synced to the server in the background, and merged field by field
// (see merge.js) so a phone and a laptop never undo each other. Plus the spaced-review schedule.
import { merge, blank } from "./merge.js";
export { merge };

const KEY = "gt.progress.v1";
export const INTERVALS = [1, 3, 7, 14, 30, 60]; // days until the next review, by box
const DAY = 864e5;
const ROLLOVER = 4;                             // a "study day" runs from 4 am to 4 am: a late session still counts as today

export let state = blank();
const subs = new Set();
let pushTimer = null, online = null, lastSync = 0, dirty = false, busy = false, skew = 0, undoAt = 0;
const now = () => Date.now() + skew;            // this device's clock, corrected to the server's

const local = {
  read() { try { return JSON.parse(localStorage.getItem(KEY)) || null; } catch { return null; } },
  // another tab may have written since we last read: fold its copy in rather than overwrite it
  write() { try { state = merge(state, this.read()); localStorage.setItem(KEY, JSON.stringify(state)); } catch { /* private mode: keep going in memory */ } },
};

export const onChange = (fn) => (subs.add(fn), () => subs.delete(fn));
const emit = () => subs.forEach((fn) => fn(state));
/** "saving" while a change is waiting or on its way, "synced" after the server confirmed, "local" when it could not be reached. */
export const syncStatus = () => ({ online, lastSync, mode: online === false ? "local" : dirty || busy || online === null ? "saving" : "synced", undoAt });
const signedOut = () => { location.href = "/login" + (location.hash || ""); };

function took(body) {                           // what every /api/progress answer carries
  if (typeof body.now === "number") skew = body.now - Date.now();
  undoAt = body.undo || 0;
  return body.state;
}

/** What this browser already knows. Synchronous, so the first screen never waits for the network. */
export function initLocal() { state = merge(blank(), local.read()); emit(); }

/** Fetch the server's copy, merge, and send back anything this device had that the server did not. */
export async function sync() {
  try {
    const r = await fetch("/api/progress", { credentials: "same-origin", signal: AbortSignal.timeout?.(10000) });
    if (r.status === 401) return void signedOut();
    if (!r.ok) throw new Error(r.status);
    const remote = took(await r.json());
    const before = JSON.stringify(state);
    state = merge(state, remote);
    local.write();
    online = true; lastSync = Date.now();
    if (JSON.stringify(merge(blank(), remote)) !== JSON.stringify(state)) { dirty = true; schedulePush(200); }   // this device had newer records
    emit();
    return before !== JSON.stringify(state);
  } catch { online = false; emit(); return false; }
}
export async function init() { initLocal(); await sync(); }

function schedulePush(ms = 4000) {
  clearTimeout(pushTimer);
  pushTimer = setTimeout(push, ms);
}
export async function push(keepalive = false) {
  clearTimeout(pushTimer); pushTimer = null;
  busy = true;
  try {
    const r = await fetch("/api/progress", { method: "PUT", credentials: "same-origin", keepalive, headers: { "content-type": "application/json" }, body: JSON.stringify({ state }) });
    if (r.status === 401) return void signedOut();
    if (!r.ok) throw new Error(r.status);
    const remote = took(await r.json());
    if (remote) { state = merge(state, remote); local.write(); }
    online = true; dirty = false; lastSync = Date.now();
  } catch { online = false; dirty = true; schedulePush(30000); }      // always try again, also for a save that died as the tab was hidden
  busy = false;
  emit();
}
addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") { if (pushTimer || dirty) push(true); }
  else sync();                                  // back on this tab: another device may have moved on
});
addEventListener("online", () => schedulePush(500));
addEventListener("storage", (e) => { if (e.key === KEY) { state = merge(state, local.read()); emit(); } });

export function put(coll, id, patch, { quiet = false, lazy = false } = {}) {
  state[coll][id] = { ...(state[coll][id] || {}), ...patch, t: now() };
  touchDay();
  dirty = true;
  local.write();
  if (!quiet) emit();
  schedulePush(lazy ? 20000 : 4000);
}
export function setting(key, value) {
  if (value === undefined) return state.settings?.[key];
  state.settings = { ...state.settings, [key]: value, t: now() };
  dirty = true; local.write(); emit(); schedulePush();
}

// ---------- days: calendar arithmetic with one roll-over hour, so a daylight-saving change or a late night cannot move a card ----------
const studyDay = (ms = now()) => { const d = new Date(ms - ROLLOVER * 3600e3); d.setHours(0, 0, 0, 0); return d; };
export const dayKey = (d = studyDay()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const dayOffset = (n) => { const d = studyDay(); d.setDate(d.getDate() + n); return d; };
function touchDay() { const k = dayKey(); if (!state.days[k]) state.days[k] = { t: now() }; }
const startOfToday = () => studyDay().getTime() + ROLLOVER * 3600e3;
const endOfToday = () => dayOffset(1).getTime() + ROLLOVER * 3600e3 - 1;
const dueAt = (box) => dayOffset(INTERVALS[box]).getTime() + ROLLOVER * 3600e3;

// ---------- spaced review ----------
export function answer(cardId, correct) {
  const c = state.cards[cardId] || { box: -1, n: 0, ok: 0 };
  const box = correct ? Math.min(c.box + 1, INTERVALS.length - 1) : 0;
  put("cards", cardId, { box: Math.max(box, 0), due: dueAt(Math.max(box, 0)), n: c.n + 1, ok: c.ok + (correct ? 1 : 0), last: correct ? 1 : 0, first: c.first ?? (correct ? 1 : 0), at: now() }, { quiet: true });
}
/** Put a card in the deck without counting an answer (review-only questions enter due tomorrow). */
export function seed(cardId) {
  if (!state.cards[cardId]) put("cards", cardId, { box: 0, due: dueAt(0), n: 0, ok: 0, seeded: 1 }, { quiet: true });
}
export function due(limit = Infinity) {
  const end = endOfToday();
  return Object.entries(state.cards).filter(([, c]) => (c.due || 0) <= end).sort((a, b) => a[1].due - b[1].due).slice(0, limit).map(([id]) => id);
}
export function nextDue() {
  const end = endOfToday(), later = Object.values(state.cards).map((c) => c.due || 0).filter((d) => d > end);
  return later.length ? Math.min(...later) : null;
}
export function reviewedToday() {
  const start = startOfToday();
  return Object.values(state.cards).filter((c) => c.n && (c.at || c.t) >= start).length;
}
export function stats(course) {
  const lessons = course.lessons, done = lessons.filter((l) => state.lessons[l.id]?.done).length;
  const cards = Object.values(state.cards).filter((c) => c.n);
  const mature = cards.filter((c) => c.box >= 3).length;
  const seen = cards.reduce((a, c) => a + c.n, 0), ok = cards.reduce((a, c) => a + c.ok, 0);
  const days = []; for (let i = 6; i >= 0; i--) days.push(!!state.days[dayKey(dayOffset(-i))]);
  const minutes = lessons.filter((l) => state.lessons[l.id]?.watched).reduce((a, l) => a + (l.minutes || 0), 0);
  return { done, total: lessons.length, pct: lessons.length ? Math.round((100 * done) / lessons.length) : 0, cards: cards.length, mature, accuracy: seen ? Math.round((100 * ok) / seen) : null, week: days, activeDays: days.filter(Boolean).length, minutes: Math.round(minutes), weekdayToday: studyDay().getDay() };
}
export function exportState() { return JSON.stringify(state, null, 1); }

/** Start over. Settings are kept; the server takes a copy of everything first, so it can be undone (see restore). */
export function resetAll() {
  const keep = { ...state.settings };
  state = blank(); state.settings = { ...keep, t: now(), reset: now() };
  dirty = true;
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { /* fine */ }
  emit();
  return push();
}
/** Undo the last "start over": the server restores the copy it took just before it. */
export async function restore() {
  const r = await fetch("/api/progress/restore", { method: "POST", credentials: "same-origin", headers: { "content-type": "application/json" }, body: "{}" });
  if (!r.ok) return false;
  const remote = took(await r.json());
  state = merge(blank(), remote);
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { /* fine */ }
  dirty = false; emit();
  return true;
}
