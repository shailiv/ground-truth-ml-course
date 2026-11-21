import { L, write, ghosts, sleep, clickText, fold, hideOv, reveal, ans } from "./lib.mjs";
const id = "1-1";
const seed = "__gt.store.put('lessons', '1-1', {guess: 2}); await new Promise(r => setTimeout(r, 300));";
write("c-lesson-laptop-2", [
  ...[5, 6, 7].map((n) => ({ name: `c0${n - 4}-slide${n}`, url: "/#/lesson/1-1/watch", ...L, js: `await __gt.player.show(${n}, false); ${hideOv} ${reveal} return {type: __gt.player.segments[${n}].visual.type, fit: __gt.player.slide.style.cssText};` })),
  { name: "c04-resume-overlay", url: "/#/lesson/1-1/watch", ...L, js: `return {overlay: document.querySelector('.overlay .box').innerText, ghosts: ${ghosts}};` },
  { name: "c05-transcript", url: "/#/lesson/1-1/watch", ...L, js: `${clickText("Show the transcript")} document.querySelector('.transcript').scrollIntoView({block: 'start'}); window.scrollBy(0, -140);` },
  { name: "c06-below-player", url: "/#/lesson/1-1/watch", ...L, js: `window.scrollTo(0, 99999); return ${ghosts};` },
  { name: "c07-complete", url: "/#/lesson/1-1/watch", ...L, js: `await __gt.player.show(8, false); ${hideOv} ${reveal} __gt.player.next(true); ${sleep(900)} return {banner: !document.querySelector('.done-banner').hidden, y: scrollY};` },
  { name: "c08-check-q1-before", url: "/#/lesson/1-1", ...L, js: "return {hash: location.hash, keys: document.querySelector('.keys')?.textContent};" },
  { name: "c09-check-q1-right", url: "/#/lesson/1-1/check", ...L, js: `${ans(id, 0, true)} ${sleep(300)} return scrollY;` },
  { name: "c10-check-q2-wrong", url: "/#/lesson/1-1/check", ...L, js: `${ans(id, 0, true)} ${clickText("Next question")} ${ans(id, 1, false)} ${sleep(300)} return scrollY;` },
  { name: "c11-check-keyboard", url: "/#/lesson/1-1/check", ...L, js: `document.body.dispatchEvent(new KeyboardEvent('keydown', {key: 'b', bubbles: true})); ${sleep(200)} const answered = document.querySelectorAll('.opt[disabled]').length; const focused = document.activeElement?.textContent; document.activeElement?.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true})); ${sleep(200)} return {answered, focused, label: document.querySelector('.q .concept').textContent};` },
  { name: "c12-check-score-2of4", url: "/#/lesson/1-1/check", ...L, js: `${ans(id, 0, true)} ${clickText("Next question")} ${ans(id, 1, false)} ${clickText("Next question")} ${ans(id, 2, true)} ${clickText("Next question")} ${ans(id, 3, false)} ${sleep(300)} ${clickText("Finish")} ${sleep(400)} return {banner: document.querySelector('.done-banner')?.innerText, btns: [...document.querySelectorAll('.done-banner .btn')].map(b => b.textContent + '|' + getComputedStyle(b).visibility), tabs: [...document.querySelectorAll('.steps button')].map(b => b.textContent.trim() + (b.classList.contains('done') ? ':done' : '')), cards: Object.keys(__gt.store.state.cards)};` },
], seed);
