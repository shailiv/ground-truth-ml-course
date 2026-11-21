import { L, LL, P, PL, T, S, write, ghosts, sleep, clickText } from "./lib.mjs";
const seed = `const s = __gt.store, now = Date.now(); for (const id of ['1-1','1-2','1-3']) { s.put('lessons', id, {guess: 1, watched: now, quiz: {score: 3, of: 4, t: now}, done: now}); } await new Promise(r => setTimeout(r, 400));`;
write("k-guide-about", [
  { name: "k01-guide-laptop", url: "/#/guide", ...L, js: "const r = await fetch('/data/assistant-pack.md'); const t = await r.text(); return {status: r.status, len: t.length, head: t.slice(0, 80), h2: document.querySelectorAll('.panel h2')[1].textContent, dl: document.querySelector('a[download]').getAttribute('href')};" },
  { name: "k02-guide-unlocked-open", url: "/#/guide", ...L, js: "const d = document.querySelector('details.bm'); d.open = true; d.scrollIntoView({block: 'start'}); window.scrollBy(0, -120);" },
  { name: "k03-guide-glossary-search", url: "/#/guide", ...L, js: "const q = document.querySelector('#gloss-q'); q.scrollIntoView({block: 'start'}); window.scrollBy(0, -140); q.value = 'leak'; q.dispatchEvent(new Event('input')); return document.querySelectorAll('.gloss').length;" },
  { name: "k04-guide-glossary-nomatch", url: "/#/guide", ...L, js: "const q = document.querySelector('#gloss-q'); q.value = 'zzzz'; q.dispatchEvent(new Event('input')); q.scrollIntoView({block: 'center'}); return document.querySelectorAll('.gloss').length;" },
  { name: "k05-guide-phone", url: "/#/guide", ...P },
  { name: "k06-guide-phone-s2", url: "/#/guide", ...P, js: "document.querySelector('details.bm').open = true; document.querySelectorAll('.panel')[1].scrollIntoView({block: 'start'});" },
  { name: "k07-guide-laptop-light-gloss", url: "/#/guide", ...LL, js: "document.querySelector('#gloss-q').scrollIntoView({block: 'start'}); window.scrollBy(0, -120);" },
  { name: "k08-about-laptop", url: "/#/about", ...L, js: "return {h: document.documentElement.scrollHeight, h2: [...document.querySelectorAll('.prose h2')].map(h => h.textContent)};" },
  { name: "k09-about-laptop-light-s2", url: "/#/about", ...LL, js: "window.scrollTo(0, 700);" },
  { name: "k10-settings-laptop", url: "/#/settings", ...L, js: `${sleep(400)} return {y: scrollY, ghosts: ${ghosts}, nav: [...document.querySelectorAll('.nav a')].filter(a => a.getAttribute('aria-current') === 'page').map(a => a.textContent)};` },
  { name: "k11-settings-phone", url: "/#/settings", ...P, js: `${sleep(400)} return {y: scrollY, ghosts: ${ghosts}};` },
  { name: "k12-about-phone", url: "/#/about", ...PL },
], seed);
