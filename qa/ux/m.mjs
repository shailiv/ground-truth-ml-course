import { L, LL, P, PL, T, S, write, ghosts, sleep, clickText, fold, hideOv, reveal, ans } from "./lib.mjs";
const seed = `const s = __gt.store, now = Date.now(); s.put('lessons', '1-1', {guess: 1, watched: now}); await new Promise(r => setTimeout(r, 300));`;
write("m-edges", [
  { name: "m01-lesson-missing", url: "/#/lesson/9-9", ...L, js: "return {text: document.querySelector('main').innerText, title: document.title, nav: [...document.querySelectorAll('.nav a')].filter(a => a.getAttribute('aria-current') === 'page').map(a => a.textContent)};" },
  { name: "m02-route-missing-phone", url: "/#/nonsense", ...P },
  { name: "m03-case-missing", url: "/#/case/c99", ...L, js: "return document.querySelector('main').innerText;" },
  { name: "m04-bad-step", url: "/#/lesson/1-1/banana", ...L, js: "return {hash: location.hash, sel: document.querySelector('.steps [aria-selected=true]')?.textContent};" },
  { name: "m05-back-between-steps", url: "/#/", ...L, js: `location.hash = '#/lesson/1-2'; ${sleep(600)} document.querySelectorAll('.opt')[0].click(); ${sleep(300)} ${clickText("Watch the lesson")} ${sleep(500)} const h1 = location.hash; [...document.querySelectorAll('.steps button')].find(b => b.textContent.includes('Check')).click(); ${sleep(400)} const h2 = location.hash; history.back(); ${sleep(900)} return {h1, h2, afterBack: location.hash, len: history.length};` },
  { name: "m06-check-reload-mid", url: "/#/lesson/1-1/check", ...L, js: `${ans("1-1", 0, true)} ${clickText("Next question")} ${ans("1-1", 1, false)} ${clickText("Next question")} ${sleep(200)} const before = document.querySelector('.q .concept').textContent; setTimeout(() => location.reload(), 50); return before;`, wait: 2500 },
  { name: "m07-check-after-reload", url: "/#/lesson/1-1/check", ...L, js: "return {label: document.querySelector('.q .concept')?.textContent, quiz: __gt.store.state.lessons['1-1'].quiz || null};" },
  { name: "m08-check-leave-warning", url: "/#/lesson/1-1/check", ...L, js: `${ans("1-1", 0, true)} ${clickText("Next question")} [...document.querySelectorAll('.steps button')].find(b => b.textContent.includes('Watch')).click(); ${sleep(400)} [...document.querySelectorAll('.steps button')].find(b => b.textContent.includes('Check')).click(); ${sleep(400)} return document.querySelector('.q .concept')?.textContent;` },
  { name: "m09-watch-tablet-light", url: "/#/lesson/1-1/watch", ...T, js: `await __gt.player.show(2, false); ${hideOv} ${reveal} return ${fold};` },
  { name: "m10-watch-short-laptop", url: "/#/lesson/1-1/watch", ...S, js: `await __gt.player.show(2, false); ${hideOv} ${reveal} return ${fold};` },
  { name: "m11-watch-laptop-light-table", url: "/#/lesson/1-1/watch", ...LL, js: `await __gt.player.show(2, false); ${hideOv} ${reveal}` },
  { name: "m12-watch-phone-landscape", url: "/#/lesson/1-1/watch", w: 844, h: 390, mobile: true, theme: "dark", js: `return ${fold};` },
], seed);
