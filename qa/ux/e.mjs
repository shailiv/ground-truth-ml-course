import { P, PL, write, ghosts, sleep, clickText, fold, hideOv, reveal, ans } from "./lib.mjs";
const id = "1-1";
const top = "document.querySelector('.stage-wrap').scrollIntoView({block:'start'});";
write("e-lesson-phone-1", [
  { name: "e01-p-guess-before", url: "/#/lesson/1-1", ...P, js: `return ${ghosts};` },
  { name: "e02-p-guess-wrong", url: "/#/lesson/1-1", ...P, js: `const p = __gt.course.lessons.find(l => l.id === '1-1').predict; document.querySelectorAll('.opt')[(p.answer + 2) % 4].click(); ${sleep(800)} return scrollY;` },
  { name: "e03-p-watch-arrive", url: "/#/lesson/1-1", ...P, js: `return {hash: location.hash, fold: ${fold}, overlay: document.querySelector('.overlay .box').innerText};` },
  { name: "e04-p-watch-playing-6s", url: "/#/lesson/1-1/watch", ...P, js: `document.querySelector('.bigplay').click(); ${sleep(6000)} return {time: document.querySelector('.time').textContent, paused: __gt.player.audio.paused, y: scrollY, fold: ${fold}};`, wait: 200 },
  { name: "e05-p-slide1-code-cc-light", url: "/#/lesson/1-1/watch", ...PL, js: `__gt.player.setCaptions(true); await __gt.player.show(1, false); ${hideOv} ${reveal} __gt.player.seekIn(12); ${top}` },
  { name: "e06-p-slide2-table-cc", url: "/#/lesson/1-1/watch", ...P, js: `__gt.player.setCaptions(true); await __gt.player.show(2, false); ${hideOv} ${reveal} __gt.player.seekIn(20); ${top}` },
  { name: "e07-p-slide3-stat", url: "/#/lesson/1-1/watch", ...P, js: `__gt.player.setCaptions(false); await __gt.player.show(3, false); ${hideOv} ${reveal} ${top}` },
  { name: "e08-p-slide4-compare", url: "/#/lesson/1-1/watch", ...P, js: `await __gt.player.show(4, false); ${hideOv} ${reveal} ${top}` },
  { name: "e09-p-slide5-flow", url: "/#/lesson/1-1/watch", ...P, js: `await __gt.player.show(5, false); ${hideOv} ${reveal} ${top}` },
  { name: "e10-p-listen", url: "/#/lesson/1-1/watch", ...P, js: `await __gt.player.show(2, false); ${hideOv} document.querySelector('[aria-label^="Listening mode"]').click(); ${top}` },
  { name: "e11-p-below-transcript", url: "/#/lesson/1-1/watch", ...P, js: `__gt.player.setListen(false); ${clickText("Show the transcript")} document.querySelector('.controls').scrollIntoView({block:'start'});` },
  { name: "e12-p-complete", url: "/#/lesson/1-1/watch", ...P, js: `await __gt.player.show(8, false); ${hideOv} ${reveal} __gt.player.next(true); ${sleep(900)} return scrollY;` },
]);
