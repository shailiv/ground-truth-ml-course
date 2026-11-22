// Local test harness: runs the REAL worker.js fetch handler under Node with an in-memory KV
// and the static files served from disk. No workerd needed.
//   node build/dev_server.mjs [port]      passphrase: "test"
import http from "node:http";
import worker from "../site/worker.js";
import { makeEnv, fakeClaude } from "./local_env.mjs";

// GT_FAKE_API=1 gives the local site a pretend Claude API, to look at the streamed tutor without a key
const env = makeEnv(process.env.GT_FAKE_API ? { ANTHROPIC_API_KEY: "sk-ant-local-pretend", TUTOR_FETCH: fakeClaude() } : {});
const port = +process.argv[2] || 8788;
http.createServer(async (req, res) => {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  const headers = new Headers(Object.entries(req.headers).filter(([, v]) => typeof v === "string"));
  headers.set("cf-connecting-ip", "127.0.0.1");
  const request = new Request(`http://localhost:${port}${req.url}`, { method: req.method, headers, body: ["GET", "HEAD"].includes(req.method) ? undefined : Buffer.concat(chunks), redirect: "manual" });
  try {
    const r = await worker.fetch(request, env);
    const h = {};
    r.headers.forEach((v, k) => { h[k] = k === "set-cookie" ? v.replace("; Secure", "") : v; });   // plain http locally
    res.writeHead(r.status, h);
    if (r.body && (r.headers.get("content-type") || "").includes("ndjson")) { for await (const chunk of r.body) res.write(chunk); res.end(); }
    else res.end(Buffer.from(await r.arrayBuffer()));
  } catch (e) {
    console.error(e);
    res.writeHead(500); res.end(String(e));
  }
}).listen(port, "127.0.0.1", () => console.log(`Ground Truth dev server on http://localhost:${port}  (passphrase: test)`));
