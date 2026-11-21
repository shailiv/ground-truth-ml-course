import fs from "node:fs";
export const base = "http://localhost:8791", out = "qa/ux/shots";
export const L = { w: 1366, h: 768, theme: "dark" };
export const LL = { w: 1366, h: 768, theme: "light" };
export const P = { w: 390, h: 844, mobile: true, theme: "dark" };
export const PL = { w: 390, h: 844, mobile: true, theme: "light" };
export const T = { w: 820, h: 1100, theme: "light" };
export const S = { w: 1280, h: 640, theme: "dark" };
export const reveal = "document.querySelectorAll('.cue.off').forEach(e => e.classList.remove('off'));";
export const hideOv = "document.querySelector('.overlay').hidden = true;";
export const center = "document.querySelector('.stage-wrap').scrollIntoView({block:'center'});";
export const clickText = (t) => `[...document.querySelectorAll('button, a.btn')].find(b => b.textContent.trim().startsWith(${JSON.stringify(t)})).click();`;
export const ans = (id, qi, right) => `{ const q = __gt.course.lessons.find(l => l.id === '${id}').quiz[${qi}]; [...document.querySelectorAll('.opt')].find(b => (b.querySelector('span').textContent === q.options[q.answer]) === ${right}).click(); }`;
export const sleep = (ms) => `await new Promise(r => setTimeout(r, ${ms}));`;
// where the player sits relative to the window: is the control bar on screen without scrolling?
export const fold = "(() => { const c = document.querySelector('.controls')?.getBoundingClientRect(), s = document.querySelector('.stage')?.getBoundingClientRect(); return c ? {stageTop: Math.round(s.top), stageH: Math.round(s.height), stageW: Math.round(s.width), controlsBottom: Math.round(c.bottom), vh: innerHeight, cut: Math.max(0, Math.round(c.bottom - innerHeight))} : null; })()";
export const ghosts = "[...document.querySelectorAll('.ghost')].map(e => e.textContent.trim().slice(0, 30) + '|' + getComputedStyle(e).visibility + '|' + getComputedStyle(e).display)";
export const write = (name, shots, seed) => fs.writeFileSync(`qa/ux/${name}.json`, JSON.stringify({ base, out, ...(seed ? { seed } : {}), shots }, null, 1));
