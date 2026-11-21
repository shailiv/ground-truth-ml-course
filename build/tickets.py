"""Build the text dataset for the 'text, embeddings and LLMs' lessons - all with Gemini.

Version 2, after the review council:
  - whole generation batches are held out for the test set (no sibling tickets on both sides)
  - the test tickets are written by a DIFFERENT model than the training tickets
  - a third of all tickets are deliberately hard (two tangled issues, vague wording)
  - the zero-shot classifier is given its own plain category descriptions, not the generator's
  - the test set is 300 tickets, so differences between methods can be told from noise
Everything is cached in data/tickets_raw.json; delete the file to regenerate.
The numbers are computed afterwards by build/tickets_analysis.py (scikit-learn under Pyodide).
"""
import concurrent.futures as cf
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path.home() / ".claude" / "skills" / "gemini" / "scripts"))
import gemini as G  # noqa: E402

OUT = pathlib.Path("data/tickets_raw.json")
# what the WRITER is told
CATS = {
    "billing": "invoices, charges, refunds, payment methods, credit, spending caps on the bill",
    "tracking_setup": "installing or debugging the conversion pixel / tag / server-side events; conversions not being recorded",
    "ad_review": "ads or campaigns rejected, stuck in review, or flagged for policy reasons",
    "performance": "results are poor or got worse: high CPA, low conversions, falling CTR, budget not delivering",
    "account_access": "cannot log in, lost access, user permissions, two-factor problems",
    "feature_request": "asking for a capability the product does not have, or suggesting an improvement",
}
# what the CLASSIFIER is told - written separately, in different words
LABEL_GUIDE = {
    "billing": "money owed or paid: what they were charged, receipts, getting money back, how they pay",
    "tracking_setup": "measurement is not working: sales or sign-ups are not showing up in reports, tag problems",
    "ad_review": "an ad is not allowed to run or is waiting for approval",
    "performance": "the ads run and are measured, but the results are disappointing",
    "account_access": "they cannot get into the product, or someone has the wrong permissions",
    "feature_request": "they want the product to do something it does not do today",
}
SEEDS = ["a small e-commerce shop owner, informal, short messages", "an agency media buyer managing many accounts, terse and technical",
         "a frustrated marketing manager, long and emotional", "a polite first-time advertiser who is unsure of the terminology",
         "a finance or operations person, formal", "a growth marketer at a mobile game studio, uses jargon and abbreviations",
         "a founder writing from a phone between meetings", "a non-native English speaker, simple sentences"]
PLAN = [("train", "fast", "normal"), ("train", "fast", "normal"), ("train", "fast", "normal"), ("train", "fast", "hard"),
        ("test", "gemini-4-neon", "normal"), ("test", "gemini-4-neon", "hard"), ("test", "gemini-4-neon", "hard")]     # per category, 25 tickets each
PER = 25


def ask_json(model, prompt, schema, system=None):
    body = {"model": G.resolve(model, model), "input": prompt, "response_format": {"type": "text", "mime_type": "application/json", "schema": schema}}
    if system:
        body["system_instruction"] = system
    for attempt in range(3):
        d = G.http("POST", "interactions", body, timeout=900)
        if d.get("status") == "completed":
            text = "".join(c.get("text", "") for s in d.get("steps", []) if s.get("type") == "model_output" for c in s.get("content", []) if c.get("type") == "text")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
    raise RuntimeError(f"no usable answer from {model}")


def write_batch(job):
    cat, b, (split, model, style) = job
    rnd = random.Random(f"{cat}-{b}")
    seeds = rnd.sample(SEEDS, 3)
    others = [c for c in CATS if c != cat]
    if style == "hard":
        twist = (f"These are the HARD ones. Every ticket must tangle the main issue with a second, different problem "
                 f"(pick from: {', '.join(others)}), give the second problem real space, and sometimes open with it - but a careful human reader "
                 f"would still say the thing the customer most needs solved is {cat}. Half should be vague or indirect about what is wrong.")
    else:
        twist = "About a third should also mention a second, different problem in passing."
    prompt = (f"Write {PER} realistic support tickets that advertisers send to the support team of a native advertising platform "
              f"(businesses buy sponsored content placements, pay per click, and track conversions).\n\n"
              f"Every ticket's MAIN issue is: {cat} - {CATS[cat]}.\n\n{twist}\n\n"
              f"Make them varied and messy like real tickets: from one line to a short paragraph; voices such as {seeds[0]}; {seeds[1]}; {seeds[2]}. "
              f"About a quarter should contain a typo or sloppy punctuation. Do not name the category, no real company or person names, "
              f"no greetings like 'Dear support', no ticket numbers. English only. Return only the ticket texts.")
    schema = {"type": "object", "properties": {"tickets": {"type": "array", "items": {"type": "string"}}}, "required": ["tickets"]}
    got = []
    for _ in range(4):                                  # a model occasionally returns an empty list: ask again
        got = ask_json(model, prompt, schema).get("tickets", [])
        if len(got) >= 20:
            break
    print(f"  wrote {cat} batch {b} ({split}, {style}, {model}): {len(got)}", flush=True)
    return [{"text": t.strip(), "label": cat, "split": split, "style": style, "batch": f"{cat}-{b}", "writer": G.resolve(model, model)} for t in got if len(t.strip()) > 15]


def generate():
    jobs = [(cat, b, plan) for cat in CATS for b, plan in enumerate(PLAN)]
    rows = []
    with cf.ThreadPoolExecutor(6) as ex:
        for part in ex.map(write_batch, jobs):
            rows += part
    seen, uniq = set(), []
    for r in rows:
        k = r["text"].lower()[:60]
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    random.Random(7).shuffle(uniq)
    for i, r in enumerate(uniq):
        r["id"] = i
    return uniq


def embed(rows):
    model = G.resolve("embed", "embed")
    rows = [r for r in rows if "emb" not in r]
    for i in range(0, len(rows), 50):
        chunk = rows[i:i + 50]
        body = {"requests": [{"model": f"models/{model}", "content": {"parts": [{"text": "task: classification | query: " + r["text"]}]},
                              "output_dimensionality": 256} for r in chunk]}
        d = G.http("POST", f"models/{model}:batchEmbedContents", body, timeout=300)
        for r, e in zip(chunk, d["embeddings"]):
            r["emb"] = [round(v, 5) for v in e["values"]]
        print(f"  embedded {i + len(chunk)}/{len(rows)}", flush=True)
    return model


def zero_shot(rows, model, key):
    test = [r for r in rows if r["split"] == "test" and key not in r]
    schema = {"type": "object", "properties": {"labels": {"type": "array", "items": {"type": "object", "properties": {
        "i": {"type": "integer"}, "label": {"type": "string", "enum": list(CATS)}}, "required": ["i", "label"]}}}, "required": ["labels"]}
    system = ("You sort advertiser support tickets. Categories:\n" + "\n".join(f"- {c}: {d}" for c, d in LABEL_GUIDE.items()) +
              "\nA ticket may mention several things. Choose the ONE the customer most needs solved.")

    def do(i):
        chunk = test[i:i + 20]
        prompt = "Label each ticket.\n\n" + "\n\n".join(f"[{j}] {r['text']}" for j, r in enumerate(chunk))
        got = {x["i"]: x["label"] for x in ask_json(model, prompt, schema, system)["labels"]}
        for j, r in enumerate(chunk):
            r[key] = got.get(j)
        print(f"  {key}: {min(i + 20, len(test))}/{len(test)}", flush=True)

    with cf.ThreadPoolExecutor(5) as ex:
        list(ex.map(do, range(0, len(test), 20)))
    return G.resolve(model, model)


if __name__ == "__main__":
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    if data.get("version") != 2:
        data = {"version": 2, "rows": generate(), "label_guide": LABEL_GUIDE}
        OUT.write_text(json.dumps(data), encoding="utf-8")
    rows = data["rows"]
    have = {r["batch"] for r in rows}
    missing = [(cat, b, plan) for cat in CATS for b, plan in enumerate(PLAN) if f"{cat}-{b}" not in have]
    for job in missing:                                 # top up any batch that came back empty
        new = write_batch(job)
        for r in new:
            r["id"] = len(rows)
            rows.append(r)
        OUT.write_text(json.dumps(data), encoding="utf-8")
    if any("emb" not in r for r in rows):
        data["embedding_model"] = embed(rows)
        data["embedding_dim"] = 256
        OUT.write_text(json.dumps(data), encoding="utf-8")
    for model, key in (("cheap", "llm_cheap"), ("default", "llm_default")):
        if any(key not in r for r in rows if r["split"] == "test"):
            data[key + "_model"] = zero_shot(rows, model, key)
            OUT.write_text(json.dumps(data), encoding="utf-8")
    n_test = sum(r["split"] == "test" for r in rows)
    print(f"tickets: {len(rows)} ({n_test} held out, {sum(r['style'] == 'hard' for r in rows)} hard); writers:", sorted({r['writer'] for r in rows}))
    for key in ("llm_cheap", "llm_default"):
        acc = sum(r.get(key) == r["label"] for r in rows if r["split"] == "test") / n_test
        print(f"  zero-shot {data[key + '_model']}: accuracy {acc:.3f}")
