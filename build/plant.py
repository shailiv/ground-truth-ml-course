"""Calibrating the reviewers. A review that finds nothing proves nothing unless you know what it would have found.

This copies every lesson into qa/blind/lessons/ and, in a sample of them, PLANTS known errors:
  - numeric: a figure in the narration or on a slide is changed (digits swapped or shifted) so it contradicts facts.json
  - conceptual: one false sentence about machine learning is appended to a narration segment
The answer key goes to qa/planted_key.json (never shown to a reviewer). Every reviewer - Gemini and Claude - reads the
blind copies; build/score_reviews.py then reports what share of the planted errors each one caught.

  python build/plant.py            (deterministic: same plants every run)
"""
import json, random, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "content/lessons", ROOT / "qa/blind/lessons"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(20261121)
NUM = re.compile(r"(?<![\w.,\[])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,\[])\d+\.\d+|(?<![\w.,\[])\d{2,}")

# false statements a practitioner should reject on sight, one per chosen lesson
FALSE = {
    "2-2": "Recall, remember, is the share of your flags that turn out to be right, so a model with high recall rarely wastes a call.",
    "2-3": "An AUC of 0.85 simply means the model's yes-or-no answer is correct for 85 percent of advertisers.",
    "2-6": "A 95 percent interval tells you that 95 percent of the advertisers in the test set fall inside that range.",
    "3-2": "And because the weights come from the data, a large positive weight proves that the column causes the outcome.",
    "4-1": "The safe rule is that a deeper tree never does worse on new advertisers, it just takes longer to train.",
    "4-2": "It is fine to try several settings against the test months and keep the best, as long as you report the winning score.",
    "5-1": "Once you have adjusted for the other columns in the table, whatever gap is left is the causal effect of the practice.",
    "5-2": "With a randomised experiment you no longer need a comparison group, because randomising removes the noise.",
    "6-2": "Shuffling the days before you split is the fairest way to test a forecast, because it removes the calendar's influence.",
    "7-1": "The clustering algorithm also tells you the correct number of segments, so there is no judgement in choosing it.",
}
NUMERIC = ["1-4", "2-1", "2-2", "2-4", "2-5", "3-1", "3-3", "4-3", "4-5", "5-3", "5-5", "5-6", "6-1", "6-3", "6-4", "7-3"]

def mutate(tok):
    t = list(tok); idx = [i for i, c in enumerate(t) if c.isdigit()]
    lead = idx[0]
    for _ in range(20):
        u = t[:]
        if len(idx) >= 2 and random.random() < 0.4:
            a = random.randrange(len(idx) - 1)
            u[idx[a]], u[idx[a + 1]] = u[idx[a + 1]], u[idx[a]]
        else:
            i = random.choice(idx[: max(1, len(idx) - 1)] if len(idx) > 2 else idx)     # not only the last digit of a long number
            u[i] = str((int(u[i]) + random.choice([2, 3, 4, -2, -3])) % 10)
        new = "".join(u)
        a, b = float(tok.replace(",", "")), float(new.replace(",", ""))
        if u[lead] != "0" or "." in tok[: lead + 2]:
            if a and abs(a - b) / abs(a) >= 0.08 and not new.startswith("00"): return new
    return None

key = []
for f in sorted(SRC.glob("*.json")):
    les = json.loads(f.read_text(encoding="utf-8"))
    lid = les["id"]
    if lid in NUMERIC:
        spots = []
        for si, s in enumerate(les["segments"]):
            for m in NUM.finditer(s["narration"]): spots.append(("narration", si, None, m.start(), m.end(), m.group(0)))
            v = s["visual"]
            for field in ("rows", "items", "stats", "bars", "columns_data"):
                pass
            blob = json.dumps(v, ensure_ascii=False)
            for m in NUM.finditer(blob):
                if v.get("type") in ("widget", "code", "line", "timeline", "title"): continue
                spots.append(("visual", si, blob, m.start(), m.end(), m.group(0)))
        random.shuffle(spots)
        done, used = 0, set()
        for kind, si, blob, a, b, tok in spots:
            if done >= 3: break
            if (kind, si) in used or float(tok.replace(",", "")) < 13 and "." not in tok: continue
            new = mutate(tok)
            if not new: continue
            if kind == "narration":
                n = les["segments"][si]["narration"]
                if n.count(tok) != 1: continue
                les["segments"][si]["narration"] = n[:a] + new + n[b:]
                ctx = n[max(0, a - 50): b + 30]
            else:
                if blob.count(tok) != 1: continue
                try: les["segments"][si]["visual"] = json.loads(blob[:a] + new + blob[b:])
                except Exception: continue
                ctx = blob[max(0, a - 60): b + 30]
            used.add((kind, si)); done += 1
            key.append({"lesson": lid, "type": "number", "where": f"seg{si + 1} {kind}", "was": tok, "now": new, "context": ctx})
    if lid in FALSE:
        si = min(len(les["segments"]) - 3, 3 + random.randrange(2))
        les["segments"][si]["narration"] = les["segments"][si]["narration"].rstrip() + " " + FALSE[lid]
        key.append({"lesson": lid, "type": "concept", "where": f"seg{si + 1} narration", "now": FALSE[lid]})
    (OUT / f.name).write_text(json.dumps(les, ensure_ascii=False, indent=1), encoding="utf-8")

(ROOT / "qa/planted_key.json").write_text(json.dumps(key, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{len(key)} errors planted in {len({k['lesson'] for k in key})} of {len(list(SRC.glob('*.json')))} lessons "
      f"({sum(k['type'] == 'number' for k in key)} numeric, {sum(k['type'] == 'concept' for k in key)} conceptual)")
