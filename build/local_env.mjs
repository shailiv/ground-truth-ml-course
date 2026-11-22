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

const PRETEND_ANSWER = [
  "Because the model is graded on **past** rows, ", "where the answer already sits in the table. ",
  "On the day you score live advertisers, ", "that column is empty.\n\n",
  "- first check: `snapshot_date`\n", "- second check: the join\n\n",
  "Which column in *your own* table would fail that test, at 5 * 3 rows?",
];

/** A stand-in for Claude's API that writes an answer in slow pieces, for looking at the streamed tutor locally
 *  (GT_FAKE_API=1 node build/dev_server.mjs). It speaks the event stream the official SDK reads. */
export function fakeClaude(pieces = PRETEND_ANSWER, delay = 350) {
  return async () => {
    const enc = new TextEncoder(), ev = (o) => enc.encode(`event: ${o.type}\ndata: ${JSON.stringify(o)}\n\n`);
    const body = new ReadableStream({
      async start(c) {
        c.enqueue(ev({ type: "message_start", message: { id: "msg_local", type: "message", role: "assistant", model: "claude-opus-5-5", content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 4000, output_tokens: 1 } } }));
        c.enqueue(ev({ type: "content_block_start", index: 0, content_block: { type: "text", text: "" } }));
        for (const text of pieces) { await new Promise((r) => setTimeout(r, delay)); c.enqueue(ev({ type: "content_block_delta", index: 0, delta: { type: "text_delta", text } })); }
        c.enqueue(ev({ type: "content_block_stop", index: 0 }));
        c.enqueue(ev({ type: "message_delta", delta: { stop_reason: "end_turn", stop_sequence: null }, usage: { output_tokens: 60 } }));
        c.enqueue(ev({ type: "message_stop" }));
        c.close();
      },
    });
    return new Response(body, { headers: { "content-type": "text/event-stream" } });
  };
}
