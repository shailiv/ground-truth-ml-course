import { L, LL, P, PL, T, S, write, ghosts, sleep, clickText } from "./lib.mjs";
const seed = `const s = __gt.store, now = Date.now(), day = 864e5; for (const l of __gt.course.lessons) { s.put('lessons', l.id, {guess: 1, watched: now - day, quiz: {score: 4, of: 4, t: now - day}, recall: 2, done: now - day}); l.review.forEach((_, k) => { s.state.cards[l.id + '-c' + k] = {box: 2, due: now + 5 * day, n: 2, ok: 2, t: now - day}; }); } for (const p of __gt.course.practice) s.put(p.kind === 'case' ? 'cases' : 'labs', p.id, {done: now}); for (const m of __gt.course.modules) s.put('missions', m.n, {done: true}); await new Promise(r => setTimeout(r, 800));`;
write("n-finished-login", [
  { name: "n01-login-laptop-dark", url: "/login", ...L, js: "return {title: document.title, focused: document.activeElement?.id};" },
  { name: "n02-login-wrong-phone-light", url: "/login?wrong=1#wrong", ...PL },
  { name: "n03-home-finished-laptop", url: "/#/", ...L, js: "return {hero: document.querySelector('.hero').innerText, side: document.querySelector('.home-side .side-card').innerText, howto: !!document.querySelector('.howto')};" },
  { name: "n04-home-finished-phone", url: "/#/", ...P },
  { name: "n05-home-finished-laptop-light-s2", url: "/#/", ...LL, js: "window.scrollTo(0, 420);" },
  { name: "n06-guide-all-unlocked", url: "/#/guide", ...L, js: "document.querySelectorAll('.panel')[1].scrollIntoView({block: 'start'}); window.scrollBy(0, -80); return document.querySelectorAll('.panel h2')[1].textContent;" },
  { name: "n07-drills-all-phone", url: "/#/drills", ...P, js: "window.scrollTo(0, 500); return document.querySelectorAll('.audio-card').length;" },
  { name: "n08-theme-toggle", url: "/#/practice", ...L, js: `document.querySelector('#theme').click(); ${sleep(300)} const t = document.documentElement.dataset.theme; return {theme: t, label: document.querySelector('#theme').getAttribute('aria-label')};` },
  { name: "n09-tutor-open-url", url: "/#/lesson/1-1/take", ...L, js: `let opened = null; window.open = (u) => { opened = u; return null; }; ${clickText("Ask Claude")} ${sleep(500)} const toast = document.querySelector('.toast')?.textContent; window.scrollTo(0, 99999); return {len: opened?.length, head: opened?.slice(0, 60), toast};` },
  { name: "n10-review-one-due-phone-light", url: "/#/", ...PL, js: `__gt.store.state.cards['1-1-c0'].due = Date.now() - 1000; location.hash = '#/review'; ${sleep(700)} return document.querySelector('.lesson-head')?.innerText;` },
  { name: "n11-last-lesson-take", url: "/#/lesson/7-5/take", ...L, js: "return [...document.querySelectorAll('.panel .row .btn')].slice(0, 3).map(b => b.textContent + '|' + getComputedStyle(b).visibility);" },
  { name: "n12-take-tablet", url: "/#/lesson/1-5/take", ...T },
], seed);
