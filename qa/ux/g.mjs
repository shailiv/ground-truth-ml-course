import { L, LL, P, PL, S, write, ghosts, sleep, clickText, fold, hideOv, reveal } from "./lib.mjs";
const info = `(() => { const sl = __gt.player.slide; return {name: __gt.player.segments[__gt.player.i].visual.name, fit: sl.style.cssText, ranges: [...sl.querySelectorAll('input[type=range]')].map(r => [r.min, r.max, r.value, r.step]), btns: [...sl.querySelectorAll('button')].map(b => b.textContent.trim()).slice(0, 10), ghosts: ${ghosts}}; })()`;
const setRange = (v) => `{ const r = __gt.player.slide.querySelector('input[type=range]'); r.value = ${v}; r.dispatchEvent(new Event('input', {bubbles: true})); r.dispatchEvent(new Event('change', {bubbles: true})); }`;
const top = "document.querySelector('.stage-wrap').scrollIntoView({block:'start'});";
write("g-widgets", [
  { name: "g01-w41-laptop-dark", url: "/#/lesson/4-1/watch", ...L, js: `await __gt.player.show(1, false); ${hideOv} ${reveal} ${sleep(500)} return ${info};` },
  { name: "g02-w41-laptop-dark-deep", url: "/#/lesson/4-1/watch", ...L, js: `await __gt.player.show(1, false); ${hideOv} ${reveal} ${sleep(300)} ${setRange(10)} ${sleep(600)}` },
  { name: "g03-w41-laptop-light", url: "/#/lesson/4-1/watch", ...LL, js: `await __gt.player.show(1, false); ${hideOv} ${reveal} ${sleep(300)} ${setRange(6)} ${sleep(600)}` },
  { name: "g04-w41-ended-continue", url: "/#/lesson/4-1/watch", ...L, js: `await __gt.player.show(1, false); ${hideOv} ${reveal} __gt.player.playing = true; __gt.player.segmentEnded(); ${sleep(400)} return {more: !__gt.player.moreEl.hidden, text: __gt.player.moreEl.innerText};` },
  { name: "g05-w41-phone-dark", url: "/#/lesson/4-1/watch", ...P, js: `await __gt.player.show(1, false); ${hideOv} ${reveal} ${sleep(500)} ${top} return ${info};` },
  { name: "g06-w41-phone-ended", url: "/#/lesson/4-1/watch", ...P, js: `await __gt.player.show(1, false); ${hideOv} ${reveal} __gt.player.segmentEnded(); ${sleep(400)} ${top}` },
  { name: "g07-w23-laptop-dark", url: "/#/lesson/2-3/watch", ...L, js: `await __gt.player.show(2, false); ${hideOv} ${reveal} ${sleep(500)} return ${info};` },
  { name: "g08-w23-laptop-moved", url: "/#/lesson/2-3/watch", ...L, js: `await __gt.player.show(2, false); ${hideOv} ${reveal} ${sleep(300)} { const r = __gt.player.slide.querySelector('input[type=range]'); r.value = +r.min + (+r.max - +r.min) * 0.2; r.dispatchEvent(new Event('input', {bubbles: true})); } ${sleep(600)}` },
  { name: "g09-w23-laptop-light", url: "/#/lesson/2-3/watch", ...LL, js: `await __gt.player.show(2, false); ${hideOv} ${reveal} ${sleep(500)}` },
  { name: "g10-w23-phone-dark", url: "/#/lesson/2-3/watch", ...P, js: `await __gt.player.show(2, false); ${hideOv} ${reveal} ${sleep(500)} ${top}` },
  { name: "g11-w23-phone-light-s2", url: "/#/lesson/2-3/watch", ...PL, js: `await __gt.player.show(2, false); ${hideOv} ${reveal} ${sleep(500)} ${top} window.scrollBy(0, 330);` },
  { name: "g12-w41-short-laptop", url: "/#/lesson/4-1/watch", ...S, js: `await __gt.player.show(1, false); ${hideOv} ${reveal} ${sleep(500)} return ${fold};` },
]);
