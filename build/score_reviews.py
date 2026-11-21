"""Score every reviewer against the planted errors, and separate the planted catches from the real findings.

  python build/score_reviews.py     -> qa/review_scores.json (who caught what), qa/findings_real.json (to adjudicate)

A reviewer "caught" a planted number if one of its findings in that lesson quotes the planted value (or the true value
it replaced) for that segment; it caught a planted false statement if a finding quotes a run of its words.
Everything else a reviewer reported is a real finding about the course and goes to adjudication.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
key = json.loads((ROOT / "qa/planted_key.json").read_text(encoding="utf-8"))

def norm(s): return re.sub(r"[^a-z0-9. ]+", " ", str(s).lower().replace(",", ""))

reviewers = {}
g = ROOT / "qa/factcheck/gemini"
if g.exists():
    fs = []
    for f in sorted(g.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for i in d.get("issues", []): fs.append({"lesson": f.stem, **i, "problem": i.get("explanation", "")})
    reviewers["gemini"] = {"findings": fs, "lessons": [f.stem for f in sorted(g.glob("*.json"))]}
for f in sorted((ROOT / "qa/redteam").glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    reviewers[d.get("reviewer", f.stem)] = {"findings": d.get("findings", []), "lessons": d.get("lessons", []), "extra": {k: d[k] for k in ("arc", "scores", "notes", "clean") if k in d}}

def seg_of(where):
    m = re.search(r"seg\s*(\d+)", str(where), re.I)
    return m.group(1) if m else None

def caught(plant, finding):
    if finding.get("lesson") != plant["lesson"]: return False
    text = norm(" ".join(str(finding.get(k, "")) for k in ("quote", "problem", "explanation", "evidence", "fix")))
    if plant["type"] == "number":
        now, was = norm(plant["now"]).strip(), norm(plant["was"]).strip()
        same_seg = seg_of(finding.get("where")) in (None, seg_of(plant["where"]))
        has = lambda v: re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", text) is not None
        return has(now) and (same_seg or has(was))
    words = norm(plant["now"]).split()
    shingles = {" ".join(words[i:i + 5]) for i in range(len(words) - 4)}
    return any(s in text for s in shingles)

scores, real = {}, []
for name, r in reviewers.items():
    mine = [p for p in key if p["lesson"] in r["lessons"]]
    used = set()
    rows = []
    for p in mine:
        hits = [i for i, f in enumerate(r["findings"]) if caught(p, f)]
        used.update(hits)                      # every finding about a planted value is a catch, never a real finding
        rows.append({**p, "caught": bool(hits)})
    num = [x for x in rows if x["type"] == "number"]; con = [x for x in rows if x["type"] == "concept"]
    scores[name] = {"lessons": len(r["lessons"]), "findings": len(r["findings"]), "planted": len(rows), "caught": sum(x["caught"] for x in rows),
                    "numbers": f"{sum(x['caught'] for x in num)}/{len(num)}", "concepts": f"{sum(x['caught'] for x in con)}/{len(con)}",
                    "missed": [{k: x[k] for k in ("lesson", "where", "type", "now") if k in x} | ({"was": x["was"]} if "was" in x else {}) for x in rows if not x["caught"]]}
    for i, f in enumerate(r["findings"]):
        if i not in used: real.append({"reviewer": name, **f})

real.sort(key=lambda f: (f.get("lesson", ""), {"high": 0, "medium": 1, "low": 2}.get(f.get("severity"), 3)))
(ROOT / "qa/review_scores.json").write_text(json.dumps(scores, indent=1, ensure_ascii=False), encoding="utf-8")
(ROOT / "qa/findings_real.json").write_text(json.dumps(real, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{'reviewer':<12}{'lessons':>8}{'planted':>9}{'caught':>8}{'numbers':>10}{'concepts':>10}{'real findings':>15}")
for name, s in scores.items():
    print(f"{name:<12}{s['lessons']:>8}{s['planted']:>9}{s['caught']:>8}{s['numbers']:>10}{s['concepts']:>10}{sum(1 for f in real if f['reviewer'] == name):>15}")
tot_p = sum(s["planted"] for n, s in scores.items() if n.startswith("expert")); tot_c = sum(s["caught"] for n, s in scores.items() if n.startswith("expert"))
if tot_p: print(f"Claude experts together: {tot_c}/{tot_p} planted errors caught ({100 * tot_c / tot_p:.0f}%)")
# union: a planted error counts as caught if ANY fact-checking reviewer caught it
both = {}
for name, r in reviewers.items():
    if name.startswith("learner"): continue
    for p in key:
        if p["lesson"] in r["lessons"]:
            k = (p["lesson"], p["where"], p["now"])
            both[k] = both.get(k, False) or any(caught(p, f) for f in r["findings"])
if both: print(f"Fact-checkers combined (Gemini or a Claude expert): {sum(both.values())}/{len(both)} planted errors caught; missed by all: {[k for k, v in both.items() if not v]}")
by = {}
for f in real: by.setdefault(f.get("severity", "?"), 0); by[f.get("severity", "?")] += 1
print(f"real findings to adjudicate: {len(real)}  {by}")
