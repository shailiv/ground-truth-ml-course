import { P, PL, write, ghosts, sleep, clickText, ans } from "./lib.mjs";
const id = "1-1";
const seed = "const s = __gt.store, now = Date.now(); s.put('lessons', '1-1', {guess: 2, watched: now}); await new Promise(r => setTimeout(r, 300));";
write("f-lesson-phone-2", [
  { name: "f01-p-check-q1", url: "/#/lesson/1-1", ...P, js: "return {hash: location.hash, keys: getComputedStyle(document.querySelector('.keys')).display};" },
  { name: "f02-p-check-q1-wrong", url: "/#/lesson/1-1/check", ...P, js: `${ans(id, 0, false)} ${sleep(600)} return scrollY;` },
  { name: "f03-p-check-q1-wrong-top", url: "/#/lesson/1-1/check", ...P, js: `${ans(id, 0, false)} ${sleep(600)} window.scrollTo(0, 0);` },
  { name: "f04-p-check-score", url: "/#/lesson/1-1/check", ...P, js: `${ans(id, 0, true)} ${clickText("Next question")} ${ans(id, 1, true)} ${clickText("Next question")} ${ans(id, 2, true)} ${clickText("Next question")} ${ans(id, 3, false)} ${sleep(300)} ${clickText("Finish")} ${sleep(400)} return [...document.querySelectorAll('.done-banner .btn')].map(b => b.textContent + '|' + getComputedStyle(b).display);` },
  { name: "f05-p-check-allfour-light", url: "/#/lesson/1-1/check", ...PL, js: `${ans(id, 0, true)} ${clickText("Next question")} ${ans(id, 1, true)} ${clickText("Next question")} ${ans(id, 2, true)} ${clickText("Next question")} ${ans(id, 3, true)} ${sleep(300)} ${clickText("Finish")} ${sleep(400)}` },
  { name: "f06-p-explain", url: "/#/lesson/1-1/explain", ...P, js: `return ${ghosts};` },
  { name: "f07-p-explain-shown", url: "/#/lesson/1-1/explain", ...P, js: `${clickText("Show a strong answer")} ${sleep(300)} window.scrollTo(0, 99999); return scrollY;` },
  { name: "f08-p-take-top", url: "/#/lesson/1-1/take", ...P },
  { name: "f09-p-take-s2", url: "/#/lesson/1-1/take", ...P, js: "window.scrollTo(0, 760);" },
  { name: "f10-p-take-s3", url: "/#/lesson/1-1/take", ...P, js: "window.scrollTo(0, 1560);" },
  { name: "f11-p-take-bottom-light", url: "/#/lesson/1-1/take", ...PL, js: "window.scrollTo(0, 99999);" },
  { name: "f12-p-home-after-one", url: "/#/", ...P },
], seed);
