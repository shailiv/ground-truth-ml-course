// The tutor, answered by the Claude API directly.
//
// When the Worker has an API key (secret ANTHROPIC_API_KEY), a question asked in a lesson goes straight from here to
// Claude and the answer streams back into the page: no relay, no machine of the owner's, phone included. The key
// belongs to the Console organization linked to the owner's Claude plan, whose monthly included API credit pays for
// it; with no card on file there, requests stop when the credit is used up and nothing is charged.
//
// Without a key this file does nothing and the relay (tutor.js) or the "open in Claude" link take over.
import Anthropic from "@anthropic-ai/sdk";
import { TUTOR_SYSTEM } from "./tutor_prompt.js";

export const API_LIMITS = { question: 2000, lesson: 12000, moment: 4000, turns: 8, turn: 3000, perDay: 150, perMonth: 2000, maxTokens: 4000 };
const DEFAULT_MODEL = "claude-opus-5-5";
const cut = (x, n) => (typeof x === "string" ? Array.from(x).slice(0, n).join("") : "");
const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });

export const apiOn = (env) => typeof env.ANTHROPIC_API_KEY === "string" && env.ANTHROPIC_API_KEY.length > 0;

/** The page's conversation as API messages: strictly alternating, starting with the learner, ending with the new question. */
export function toMessages(history, moment, question) {
  const out = [];
  for (const t of (Array.isArray(history) ? history : []).slice(-API_LIMITS.turns)) {
    const role = t?.role === "tutor" ? "assistant" : "user", text = cut(t?.text, API_LIMITS.turn).trim();
    if (!text) continue;
    if (!out.length && role === "assistant") continue;                       // a conversation starts with the learner
    if (out.length && out.at(-1).role === role) out.at(-1).content += "\n\n" + text; else out.push({ role, content: text });
  }
  if (out.length && out.at(-1).role === "user") out.pop();                   // an unanswered earlier question is superseded by this one
  const now = (moment ? "<moment>\n" + moment + "\n</moment>\n\n" : "") + "My question: " + question;
  out.push({ role: "user", content: now });
  return out;
}

/** A ceiling per day and per month, so a page stuck in a loop cannot drain the month's credit. Approximate by design. */
async function underCeiling(env, now) {
  if (!env.PROGRESS) return { ok: true };
  const day = new Date(now).toISOString().slice(0, 10), month = day.slice(0, 7);
  const perDay = +env.TUTOR_PER_DAY || API_LIMITS.perDay, perMonth = +env.TUTOR_PER_MONTH || API_LIMITS.perMonth;
  const [d, m] = await Promise.all([env.PROGRESS.get("tutor:n:day:" + day), env.PROGRESS.get("tutor:n:month:" + month)]);
  if ((+d || 0) >= perDay) return { ok: false, message: `That is the tutor's limit for one day (${perDay} questions). “Open in Claude” still works.` };
  if ((+m || 0) >= perMonth) return { ok: false, message: `That is the tutor's limit for this month (${perMonth} questions). “Open in Claude” still works.` };
  await Promise.all([
    env.PROGRESS.put("tutor:n:day:" + day, String((+d || 0) + 1), { expirationTtl: 3 * 86400 }),
    env.PROGRESS.put("tutor:n:month:" + month, String((+m || 0) + 1), { expirationTtl: 40 * 86400 }),
  ]);
  return { ok: true };
}

/** What to tell the learner when the API says no. Decided by the SDK's error classes, never by matching message text. */
export function explain(e) {
  if (e instanceof Anthropic.AuthenticationError) return "The tutor's Claude API key was not accepted. Run add-tutor-key again with a fresh key.";
  if (e instanceof Anthropic.PaymentRequiredError || e?.type === "billing_error") return "This month's included API credit is used up. It refills with your next plan payment; until then “Open in Claude” still works.";
  if (e instanceof Anthropic.PermissionDeniedError) return "The tutor's Claude API key is not allowed to do this. Check the key in the Claude Console.";
  if (e instanceof Anthropic.RateLimitError) return "Claude is asking the tutor to slow down. Try again in a minute.";
  // a 400 carries the API's own words, which is how a credit or spend-limit notice arrives: pass them on as they are
  if (e instanceof Anthropic.BadRequestError) return "Claude's API refused the request: " + cut(String(e.message || ""), 220);
  if (e instanceof Anthropic.APIConnectionError) return "The tutor could not reach Claude. Try again.";
  if (e instanceof Anthropic.APIError) return "Claude's API is busy right now. Try again in a minute.";
  return "The tutor could not answer just now. Try again.";
}

/**
 * Answer one question. The reply is a stream of lines, each a small JSON object:
 *   {"t":"delta","text":"..."}   a piece of the answer, as Claude writes it
 *   {"t":"done", ...}            finished
 *   {"t":"error","message":".."} it failed; the message is safe to show
 */
export async function answerWithApi(env, body, ctx) {
  const question = cut(body?.question, API_LIMITS.question).trim();
  if (!question) return json({ error: "empty" }, 400);
  const gate = await underCeiling(env, Date.now());
  if (!gate.ok) return json({ error: "limit", message: gate.message }, 429);

  const lesson = cut(body.lesson, API_LIMITS.lesson), moment = cut(body.moment, API_LIMITS.moment);
  const model = env.TUTOR_MODEL || DEFAULT_MODEL;
  const params = {
    model, max_tokens: API_LIMITS.maxTokens,
    // the tutor's standing instructions, then the lesson itself. The lesson is the same for every question asked in
    // it, so it is marked for caching: follow-up questions within a few minutes cost a fraction of the first.
    system: [{ type: "text", text: TUTOR_SYSTEM }, ...(lesson ? [{ type: "text", text: "<lesson>\n" + lesson + "\n</lesson>", cache_control: { type: "ephemeral" } }] : [])],
    messages: toMessages(body.history, moment, question),
  };
  // a tutor's answer should arrive quickly: moderate effort by default on the default model
  const effort = env.TUTOR_EFFORT || (env.TUTOR_MODEL ? "" : "medium");
  if (effort) params.output_config = { effort };

  const client = new Anthropic({ apiKey: env.ANTHROPIC_API_KEY, maxRetries: 1, timeout: 90_000, ...(env.TUTOR_FETCH ? { fetch: env.TUTOR_FETCH } : {}) });
  const { readable, writable } = new TransformStream(), writer = writable.getWriter(), enc = new TextEncoder();
  let stream, gone = false;
  const send = (o) => writer.write(enc.encode(JSON.stringify(o) + "\n")).catch(() => { gone = true; stream?.abort(); });   // the page went away: stop paying for the answer
  const work = (async () => {
    try {
      stream = client.messages.stream(params);
      stream.on("text", (delta) => { if (!gone) send({ t: "delta", text: delta }); });
      const msg = await stream.finalMessage();
      const u = msg.usage || {};
      await send({ t: "done", stop: msg.stop_reason, model: msg.model, tokens: { in: u.input_tokens, cached: u.cache_read_input_tokens, written: u.cache_creation_input_tokens, out: u.output_tokens } });
    } catch (e) {
      if (!gone) await send({ t: "error", message: explain(e) });
    } finally {
      try { await writer.close(); } catch { /* already closed */ }
    }
  })();
  ctx?.waitUntil?.(work);
  return new Response(readable, { headers: { "content-type": "application/x-ndjson; charset=utf-8", "cache-control": "no-store", "x-accel-buffering": "no" } });
}
