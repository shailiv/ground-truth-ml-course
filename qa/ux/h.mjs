import { L, LL, P, write, ghosts, sleep, clickText } from "./lib.mjs";
const seed = `const s = __gt.store, now = Date.now(), day = 864e5; for (const id of ['1-1','1-2','1-3']) { s.put('lessons', id, {guess: 1, watched: now - day, quiz: {score: 3, of: 4, t: now - day}, done: now - day}); __gt.course.lessons.find(l => l.id === id).review.forEach((_, k) => { s.state.cards[id + '-c' + k] = {box: 0, due: now - 1000, n: 0, ok: 0, seeded: 1, t: now - day}; }); } __gt.course.triage.forEach((_, k) => { s.state.cards['t-' + k] = {box: 0, due: now - 1000, n: 0, ok: 0, seeded: 1, t: now - day}; }); const d = new Date(now - day); s.state.days[s.dayKey(d)] = {t: now - day}; s.put('lessons', '1-4', {guess: 0, seg: 3}); await new Promise(r => setTimeout(r, 600));`;
const runAll = `let n = 0; while (document.querySelector('.opt:not([disabled])') && n < 30) { document.querySelector('.opt').click(); await new Promise(r => setTimeout(r, 60)); const nx = [...document.querySelectorAll('.row.end .btn')].at(-1); nx.click(); n++; await new Promise(r => setTimeout(r, 60)); }`;
write("h-nextday", [
  { name: "h01-home-nextday-laptop", url: "/#/", ...L, js: "return {badge: document.querySelector('#due-badge').textContent, due: __gt.store.due().length, cards: Object.keys(__gt.store.state.cards).length};" },
  { name: "h02-home-nextday-laptop-light", url: "/#/", ...LL },
  { name: "h03-home-nextday-phone", url: "/#/", ...P },
  { name: "h04-home-nextday-phone-s2", url: "/#/", ...P, js: "window.scrollTo(0, 560);" },
  { name: "h05-review-q1", url: "/#/review", ...L, js: "return {head: document.querySelector('.lesson-head').innerText, label: document.querySelector('.q .concept').textContent};" },
  { name: "h06-review-q1-answered", url: "/#/review", ...L, js: `document.querySelector('.opt').click(); ${sleep(400)} return {ghosts: ${ghosts}, wrong: !!document.querySelector('.opt.wrong'), y: scrollY, reviewedToday: __gt.store.reviewedToday()};` },
  { name: "h07-review-reload-mid", url: "/#/review", ...L, js: "return {head: document.querySelector('.lesson-head')?.innerText, bars: document.querySelectorAll('.qbar i').length};" },
  { name: "h08-review-phone-q", url: "/#/review", ...P },
  { name: "h09-review-phone-answered", url: "/#/review", ...P, js: `document.querySelector('.opt').click(); ${sleep(500)} return {y: scrollY, wrong: !!document.querySelector('.opt.wrong')};` },
  { name: "h10-review-finish", url: "/#/review", ...L, js: `${runAll} ${sleep(300)} return {n, banner: document.querySelector('.done-banner')?.innerText, badge: document.querySelector('#due-badge').hidden ? 'hidden' : document.querySelector('#due-badge').textContent, stillDue: __gt.store.due().length, reviewedToday: __gt.store.reviewedToday()};` },
  { name: "h11-review-after-cap", url: "/#/review", ...L, js: "return document.querySelector('main').innerText;" },
  { name: "h12-home-after-review", url: "/#/", ...L, js: "return document.querySelector('.home-side .side-card').innerText;" },
], seed);
