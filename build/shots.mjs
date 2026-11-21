// Headless screenshot harness for QA: drives a local Chrome over the DevTools protocol against the dev server.
//   node build/shots.mjs qa/scenarios.json [filter]
// Scenario file: { base, out, shots: [{ name, url, w, h, theme, mobile, full, js, wait }] }
//   js   - evaluated in the page after it has loaded (may be async); use window.__gt
//   full - capture the whole scrolling page instead of the viewport
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [, , file, filter] = process.argv;
const cfg = JSON.parse(fs.readFileSync(file, "utf8"));
if (process.env.GT_BASE) cfg.base = process.env.GT_BASE;      // run against a server started just for this run
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9333 + Math.floor(Math.random() * 400);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "gt-shots-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "--no-first-run", "--hide-scrollbars", "--mute-audio", "--autoplay-policy=no-user-gesture-required", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function target() {
  for (let i = 0; i < 60; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* not up yet */ }
    await sleep(250);
  }
  throw new Error("Chrome did not start");
}

const ws = new WebSocket(await target());
await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let seq = 0;
const waiting = new Map(), errors = [];
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && waiting.has(d.id)) { const [res, rej] = waiting.get(d.id); waiting.delete(d.id); d.error ? rej(new Error(d.error.message)) : res(d.result); }
  if (d.method === "Runtime.exceptionThrown") errors.push(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text);
  if (d.method === "Runtime.consoleAPICalled" && ["error", "warning"].includes(d.params.type)) errors.push(d.params.type + ": " + d.params.args.map((a) => a.value ?? a.description).join(" "));
  if (d.method === "Log.entryAdded" && d.params.entry.level === "error") errors.push("log: " + d.params.entry.text + " " + (d.params.entry.url || ""));
};
const cdp = (method, params = {}) => new Promise((res, rej) => { const id = ++seq; waiting.set(id, [res, rej]); ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async (expression) => {
  const r = await cdp("Runtime.evaluate", { expression: `(async () => { ${expression} })()`, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};

await cdp("Page.enable"); await cdp("Runtime.enable"); await cdp("Log.enable");
const out = path.resolve(cfg.out || "qa/shots");
fs.mkdirSync(out, { recursive: true });

// sign in once on the local harness, then seed progress if the scenario file asks for it
await cdp("Page.navigate", { url: cfg.base + "/login" }); await sleep(600);
await evaluate(`await fetch("/login", { method: "POST", body: new URLSearchParams({ passphrase: "test" }), redirect: "manual" });`);
if (cfg.seed) { await cdp("Page.navigate", { url: cfg.base + "/" }); await sleep(1500); await evaluate(cfg.seed); await sleep(400); }

const report = [];
for (const s of cfg.shots) {
  if (filter && !s.name.includes(filter)) continue;
  const w = s.w || 1440, h = s.h || 900;
  errors.length = 0;
  await cdp("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: s.mobile ? 2 : 1, mobile: !!s.mobile });
  await cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: s.theme || "dark" }] });
  await cdp("Page.navigate", { url: "about:blank" });
  await cdp("Page.navigate", { url: cfg.base + s.url });
  await sleep(s.load || 1400);
  await evaluate(`try { localStorage.removeItem("gt.pref.theme"); } catch {} delete document.documentElement.dataset.theme;`);
  let result = null;
  if (s.js) { try { result = await evaluate(s.js); } catch (e) { errors.push("scenario js: " + e.message); } }
  await sleep(s.wait || 500);
  const m = await evaluate(`return { sw: document.documentElement.scrollWidth, iw: innerWidth, sh: document.documentElement.scrollHeight };`);
  const params = { format: "png" };
  if (s.full) params.clip = { x: 0, y: 0, width: w, height: Math.min(m.sh, 6000), scale: 1 }, params.captureBeyondViewport = true;
  const shot = await cdp("Page.captureScreenshot", params);
  fs.writeFileSync(path.join(out, s.name + ".png"), Buffer.from(shot.data, "base64"));
  const row = { name: s.name, overflowX: m.sw > m.iw ? m.sw - m.iw : 0, errors: [...errors], result };
  report.push(row);
  console.log(`${row.overflowX || row.errors.length ? "!!" : "ok"}  ${s.name}${row.overflowX ? `  horizontal overflow ${row.overflowX}px` : ""}${row.errors.length ? "  " + row.errors.join(" | ") : ""}${result != null ? "  -> " + JSON.stringify(result) : ""}`);
}
fs.writeFileSync(path.join(out, "report.json"), JSON.stringify(report, null, 1));
ws.close(); chrome.kill();
await sleep(300);
try { fs.rmSync(profile, { recursive: true, force: true }); } catch { /* Chrome may still hold a lock; the temp dir is harmless */ }
