import { L, LL, P, PL, T, write, ghosts, sleep, clickText } from "./lib.mjs";
const seed = `const s = __gt.store, now = Date.now(); for (const id of ['1-1','1-2','1-3']) { s.put('lessons', id, {guess: 1, watched: now, quiz: {score: 3, of: 4, t: now}, done: now}); } await new Promise(r => setTimeout(r, 400));`;
write("j-lab-drills", [
  { name: "j01-two-reports-open", url: "/#/practice", ...L, js: `const b = [...document.querySelectorAll('a, button')].filter(x => /handsome|plain/.test(x.textContent)).map(x => x.tagName + '|' + x.textContent.trim() + '|' + (x.getAttribute('href') || '') + '|' + (x.target || '')); const d = document.querySelector('details') || [...document.querySelectorAll('button, summary')].find(x => x.textContent.includes('What separates')); if (d?.tagName === 'DETAILS') d.open = true; else d?.click(); ${sleep(300)} window.scrollTo(0, 260); return b;` },
  { name: "j02-practice-labs-list", url: "/#/practice", ...L, js: "window.scrollTo(0, 99999);" },
  { name: "j03-lab-top-laptop", url: "/#/lab/l1", ...L, js: "const c = __gt.course.practice.find(p => p.id === 'l1'); return {files: c.files, steps: c.steps.length, h: document.documentElement.scrollHeight};" },
  { name: "j04-lab-stage-laptop", url: "/#/lab/l1", ...L, js: "document.querySelectorAll('.panel')[1].scrollIntoView({block: 'start'}); window.scrollBy(0, -70);" },
  { name: "j05-lab-bottom-laptop-light", url: "/#/lab/l1", ...LL, js: `window.scrollTo(0, 99999); return ${ghosts};` },
  { name: "j06-lab-phone-top", url: "/#/lab/l1", ...P },
  { name: "j07-lab-phone-stage", url: "/#/lab/l1", ...P, js: "document.querySelectorAll('.panel')[1].scrollIntoView({block: 'start'});" },
  { name: "j08-drills-laptop", url: "/#/drills", ...L, js: "return {cards: document.querySelectorAll('.audio-card').length, locked: [...document.querySelectorAll('.panel .lead')].map(p => p.textContent).slice(0, 8)};" },
  { name: "j09-drills-playing", url: "/#/drills", ...L, js: `document.querySelector('.audio-card .play').click(); ${sleep(6000)} const t = document.querySelector('.audio-card .time').textContent; const d = document.querySelector('details'); d.open = true; return {time: t, range: document.querySelector('.audio-card input').value};`, wait: 300 },
  { name: "j10-drills-phone", url: "/#/drills", ...P },
  { name: "j11-drills-phone-light-s2", url: "/#/drills", ...PL, js: "document.querySelector('details').open = true; window.scrollTo(0, 300);" },
  { name: "j12-drills-tablet", url: "/#/drills", ...T },
], seed);
