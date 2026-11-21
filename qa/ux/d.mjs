import { L, write, ghosts, sleep, clickText } from "./lib.mjs";
const seed = "const s = __gt.store, now = Date.now(); s.put('lessons', '1-1', {guess: 2, watched: now, quiz: {score: 2, of: 4, t: now}, done: now}); s.seed('1-1-c0'); s.seed('1-1-c1'); await new Promise(r => setTimeout(r, 300));";
write("d-lesson-laptop-3", [
  { name: "d01-explain-empty", url: "/#/lesson/1-1/explain", ...L, js: `return ${ghosts};` },
  { name: "d02-explain-shown-notyped", url: "/#/lesson/1-1/explain", ...L, js: `${clickText("Show a strong answer")} ${sleep(300)} const r = [...document.querySelectorAll('.panel .row')].at(-1).getBoundingClientRect(); return {rateRowTop: Math.round(r.top), vh: innerHeight, y: scrollY};` },
  { name: "d03-explain-typed-bottom", url: "/#/lesson/1-1/explain", ...L, js: `const ta = document.querySelector('textarea'); ta.value = 'A rule is written by a person; a model learns the weights from past examples and is judged on rows it has not seen.'; ${clickText("Show a strong answer")} window.scrollTo(0, 99999);` },
  { name: "d04-explain-rated", url: "/#/lesson/1-1/explain", ...L, js: `${clickText("Show a strong answer")} ${clickText("Partly")} ${sleep(500)} return {hash: location.hash, tabs: [...document.querySelectorAll('.steps button')].map(b => b.textContent.trim() + (b.classList.contains('done') ? ':done' : ''))};` },
  { name: "d05-take-top", url: "/#/lesson/1-1", ...L, js: `return {hash: location.hash, ghosts: ${ghosts}};` },
  { name: "d06-take-s2", url: "/#/lesson/1-1/take", ...L, js: "window.scrollTo(0, 600);" },
  { name: "d07-take-bottom", url: "/#/lesson/1-1/take", ...L, js: "window.scrollTo(0, 99999);" },
  { name: "d08-take-next-click", url: "/#/lesson/1-1/take", ...L, js: `${clickText("Next:")} ${sleep(900)} return {hash: location.hash, y: scrollY};` },
  { name: "d09-home-after-one", url: "/#/", ...L },
  { name: "d10-home-after-one-s2", url: "/#/", ...L, js: "window.scrollTo(0, 430);" },
  { name: "d11-review-after-one", url: "/#/review", ...L },
  { name: "d12-take-last-of-module", url: "/#/lesson/1-5/take", ...L, js: "window.scrollTo(0, 520); return [...document.querySelectorAll('h3')].map(h => h.textContent);" },
], seed);
