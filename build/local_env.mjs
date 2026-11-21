// The stand-in for Cloudflare used by the local server and by the tests: an in-memory KV and the static files
// read from disk. The asset stand-in is deliberately as plain as the real one: no byte ranges of its own (the
// Worker adds them) and no decoding of an encoded slash, so a test here means the same as a test on Cloudflare.
import fs from "node:fs";
import path from "node:path";
import { TutorRoom } from "../site/tutor.js";

const PUBLIC = path.resolve("site/public");
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml", ".mp3": "audio/mpeg", ".woff2": "font/woff2", ".csv": "text/csv; charset=utf-8", ".md": "text/markdown; charset=utf-8", ".png": "image/png" };

export function makeEnv(extra = {}) {
  const kv = new Map(), room = new TutorRoom();
  return {
    PASSPHRASE: "test", SESSION_SECRET: "local-dev-secret", RELAY_SECRET: "test-relay",
    TUTOR: { idFromName: () => "room", get: () => room },
    PROGRESS: {
      async get(k, type) { const v = kv.get(k); return v == null ? null : type === "json" ? JSON.parse(v) : v; },
      async put(k, v) { kv.set(k, v); },
      async delete(k) { kv.delete(k); },
      _map: kv,
    },
    ASSETS: {
      async fetch(req) {
        let p = new URL(req.url).pathname;
        if (/%|\\/.test(p)) return new Response("Not found", { status: 404 });
        const file = path.join(PUBLIC, p);
        if (!file.startsWith(PUBLIC) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return new Response("Not found", { status: 404 });
        return new Response(fs.readFileSync(file), { headers: { "content-type": TYPES[path.extname(file)] || "application/octet-stream" } });
      },
    },
    ...extra,
  };
}
