// One merge, used by the browser (store.js) and by the Worker (worker.js), so the two can never disagree.
//
// Progress is merged FIELD BY FIELD, never record by record. A phone tab that has been open since the morning
// knows less than the laptop that finished the lesson at noon; if the phone's whole record won because it was
// written later, opening a lesson there would quietly un-finish it everywhere. So: what has happened stays
// happened (done, watched, an answered card), and only "where was I" follows the most recent device.

export const COLLS = ["lessons", "cards", "cases", "labs", "days", "missions"];
export const blank = () => ({ v: 1, lessons: {}, cards: {}, cases: {}, labs: {}, days: {}, missions: {}, settings: { t: 0 } });

const obj = (x) => (x && typeof x === "object" && !Array.isArray(x) ? x : null);
const num = (x) => (typeof x === "number" && Number.isFinite(x) ? x : 0);
const first = (a, b) => (num(a) && num(b) ? Math.min(a, b) : num(a) || num(b) || undefined);   // earliest time something happened
const newer = (a, b) => (num(b?.t) > num(a?.t) ? b : a);
const older = (a, b) => (num(b?.t) < num(a?.t) ? b : a);
const tidy = (o) => { for (const k of Object.keys(o)) if (o[k] === undefined) delete o[k]; return o; };

const RULES = {
  // a lesson: finished and watched are permanent; the guess is the first one made; the quiz is the latest attempt;
  // the position in the video belongs to whichever device moved last
  lessons(a, b) {
    const n = newer(a, b), o = older(a, b);
    const quiz = obj(a.quiz) && obj(b.quiz) ? (num(b.quiz.t) > num(a.quiz.t) ? b.quiz : a.quiz) : obj(a.quiz) || obj(b.quiz) || undefined;
    return tidy({ ...o, ...n, done: first(a.done, b.done), watched: first(a.watched, b.watched), guess: o.guess ?? n.guess, quiz, recall: n.recall ?? o.recall, seg: n.seg ?? o.seg });
  },
  // a review card: the copy that has been answered more times is the truth
  cards: (a, b) => (num(b.n) > num(a.n) ? b : num(a.n) > num(b.n) ? a : newer(a, b)),
  // a case file stays audited once audited; keep the score that came with it
  cases(a, b) { const d = num(a.done) && num(b.done) ? (a.done <= b.done ? a : b) : num(a.done) ? a : num(b.done) ? b : newer(a, b); return { ...d, t: Math.max(num(a.t), num(b.t)) }; },
  labs: newer, missions: newer,           // tick boxes: the last click wins
  days: (a, b) => ({ t: first(a.t, b.t) || 0 }),
};

export function merge(a, b) {
  const out = blank();
  const sa = obj(a?.settings) || { t: 0 }, sb = obj(b?.settings) || { t: 0 };
  // "start over" is a timestamp, not a deletion: anything recorded before it is dropped on every device.
  // It is applied to each side BEFORE the two are combined. Otherwise a device that was offline during the reset
  // would hand its old "finished" back to any record that has been touched since.
  const reset = Math.max(num(sa.reset), num(sb.reset));
  const live = (rec) => (rec && num(rec.t) >= reset ? rec : null);
  for (const c of COLLS) {
    const A = obj(a?.[c]) || {}, B = obj(b?.[c]) || {};
    for (const id of new Set([...Object.keys(A), ...Object.keys(B)])) {
      if (id === "__proto__" || id === "constructor" || id === "prototype") continue;
      const x = live(obj(A[id])), y = live(obj(B[id]));
      const rec = x && y ? RULES[c](x, y) : x || y;
      if (rec) out[c][id] = { ...rec, t: Math.max(num(x?.t), num(y?.t)) };
    }
  }
  out.settings = { ...older(sa, sb), ...newer(sa, sb) };
  if (reset) out.settings.reset = reset; else delete out.settings.reset;
  return out;
}

/** The same state with its keys in a fixed order, as text: for asking "are these two the same?" */
export function canon(x) {
  return JSON.stringify(x, (k, v) => (v && typeof v === "object" && !Array.isArray(v) ? Object.fromEntries(Object.keys(v).sort().map((key) => [key, v[key]])) : v));
}

/** Server side: no timestamp from a device may lie in the future (a fast clock, or a reset "next year" that would
 *  keep deleting new work). `due` is the one field that legitimately does. */
export function clamp(state, now, slack = 5 * 60e3) {
  const fix = (o) => { for (const k of ["t", "done", "watched", "reset"]) if (num(o?.[k]) > now + slack) o[k] = now; };
  for (const c of COLLS) for (const rec of Object.values(obj(state?.[c]) || {})) { if (!obj(rec)) continue; fix(rec); if (obj(rec.quiz)) fix(rec.quiz); }
  if (obj(state?.settings)) fix(state.settings);
  return state;
}
