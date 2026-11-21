"""Number-provenance linter: every figure a lesson states about the course's simulated worlds must trace
to data/facts.json (or the widget data), either directly, as an honest rounding, or as simple arithmetic
on figures quoted in the same lesson.

  python build/lint_numbers.py            summary + every unverified number with its context
  python build/lint_numbers.py 2-3        one lesson
Writes qa/numbers_report.json. An allow-list of reviewed exceptions lives in content/number_exceptions.json
({"<lesson id>": {"<number as written>": "why it is fine"}}).

What is checked: narration, visuals, the guess question, take-aways, course-domain quiz questions,
explain-back, the assistant brief, the audit checklist, the glossary and the audio drills.
What is not: questions set in another domain (their numbers are invented scenarios by design),
"where else this applies" and "other ways", and integers below 13 (too generic to trace).
"""
import json, math, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
facts = json.loads((ROOT / "data/facts.json").read_text(encoding="utf-8"))
widgets = json.loads((ROOT / "site/public/data/widgets.json").read_text(encoding="utf-8"))
exc_path = ROOT / "content/number_exceptions.json"
EXC = json.loads(exc_path.read_text(encoding="utf-8")) if exc_path.exists() else {}

NUM = re.compile(r"(?<![\w.,])(?:[-−]\s?)?\$?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,])(?:[-−]\s?)?\$?\d+(?:\.\d+)?")

def parse(tok):
    t = tok.replace("−", "-").replace("$", "").replace(",", "").replace(" ", "")
    return float(t), (len(t.split(".")[1]) if "." in t else 0)

# ---------- what the facts contain: per top-level key, and overall ----------
def numbers(o, out):
    if isinstance(o, bool) or o is None: return
    if isinstance(o, (int, float)):
        if math.isfinite(o): out.add(float(o))
    elif isinstance(o, str):
        for m in NUM.finditer(o): out.add(parse(m.group(0))[0])
    elif isinstance(o, dict):
        for k, v in o.items():
            for m in NUM.finditer(str(k)): out.add(parse(m.group(0))[0])
            numbers(v, out)
    elif isinstance(o, list):
        if len(o) > 400 and all(isinstance(x, (int, float)) for x in o): return     # raw per-row arrays (scores, daily series)
        for v in o: numbers(v, out)

def expand(pool):
    f = set()
    for v in pool:
        f.add(abs(v))
        if abs(v) <= 1.0: f.add(abs(v) * 100)          # a share said as a percentage
        if abs(v) >= 1000: f.add(abs(v) / 1000)        # 84,570 said as "about 85 thousand"
    return sorted(f)

BY_KEY = {}
for k, v in facts.items():
    BY_KEY[k] = set(); numbers(v, BY_KEY[k])
WIDGET_KEYS = {"depth_sweep": "depth_sweep", "tree": "tree", "calibration": "calibration", "economics": "economics", "practices": "happy", "forecast": "forecast", "anomalies": "series_anomalies", "survival": "time_to_event"}
for wk, fk in WIDGET_KEYS.items():
    if wk in widgets: numbers(widgets[wk], BY_KEY.setdefault(fk, set()))
ALL = expand(set().union(*BY_KEY.values()))

# which keys each lesson is allowed to draw on: the "Evidence: -> key, key" line of its brief in the outline
OUTLINE = (ROOT / "content/OUTLINE.md").read_text(encoding="utf-8")
EVID = {}
for m in re.finditer(r"^### (\d-\d) .*?(?=^### |^## |\Z)", OUTLINE, re.S | re.M):
    body = m.group(0)
    NL = chr(10)
    ev = " ".join(re.findall(r"\*\*Evidence:\*\*(.*?)(?=" + NL + r"\*\*|\Z)", body, re.S)) + " " + " ".join(re.findall(r"→\s*([^" + NL + r"]*)", body))
    EVID[m.group(1)] = {k for k in BY_KEY if re.search(r"(?<![\w.])" + re.escape(k) + r"(?![\w])", ev)} | {"data"}

import bisect
def near(forms, x, tol):
    i = bisect.bisect_left(forms, x - tol)
    return i < len(forms) and forms[i] <= x + tol

def matches(forms, x, dec, loose):
    """x as written with `dec` decimals. Exact rounding always passes; a spoken round number gets a little slack."""
    x = abs(x)
    if near(forms, x, 10 ** (-dec) * 0.5 + 1e-9): return True
    if not loose: return False
    if dec == 0 and x >= 100 and x % 10 == 0: return near(forms, x, max(5, x * 0.03))      # "about 1,300" for 1,311
    if dec == 0 and x < 100: return near(forms, x, 1.0)                                      # "about 60 percent" for 59.6
    if dec == 1: return near(forms, x, 0.1)
    return False

# ---------- the text of a lesson that makes claims about the course's data ----------
def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k in ("type", "name", "id", "answer", "domain", "concept", "widget", "highlight", "unit", "kicker"): continue
            yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)

def claims(les):
    for i, s in enumerate(les["segments"]):
        yield f"seg{i + 1} narration", re.sub(r"\[\[\d+\]\]", " ", s["narration"])
        for t in strings(s["visual"]): yield f"seg{i + 1} visual", t
    for t in strings(les["predict"]): yield "guess", t
    for t in les["takeaways"]: yield "takeaway", t
    for q in les["quiz"]:
        if q.get("domain") == "course":
            for t in [q["q"], *q["options"], q["why"]]: yield q["id"], t
    for t in strings(les.get("recall", {})): yield "explain-back", t
    yield "brief", les["ask_assistant"]
    for t in les["audit_checklist"]: yield "audit", t
    for g in les["glossary"]: yield "glossary", g["def"]
    for d in les["drill"]: yield "drill", d["q"] + " " + d["a"]

HEDGE = re.compile(r"\b(about|roughly|around|nearly|almost|some|close to|just over|just under|over|under|more than|less than|fewer than|at least|at most|well over|a little over|approximately)\W+(?:\w+\W+){0,2}$", re.I)
SKIP_BEFORE = re.compile(r"(?:module|lesson|part|stage|step|level|line|lines|rule|version|top|k\s*=|depth|bucket|decile|fold|folds)\s*$", re.I)

def lint(les):
    found, seen = [], []
    for where, text in claims(les):
        for m in NUM.finditer(text):
            tok = m.group(0)
            x, dec = parse(tok)
            ctx = text[max(0, m.start() - 46): m.end() + 34].replace("\n", " ")
            found.append((where, tok, x, dec, ctx, text[max(0, m.start() - 40): m.start()]))
    own = expand(set().union(*[BY_KEY[k] for k in EVID.get(les["id"], {"data"})]))
    ok_vals, out, elsewhere = [], [], []
    for where, tok, x, dec, ctx, before in found:
        if dec == 0 and abs(x) < 13: continue
        if dec == 0 and 1990 <= x <= 2035: continue
        if tok in EXC.get(les["id"], {}): continue
        # an exact rounding of a figure in this lesson's own evidence passes; a looser spoken rounding passes only
        # when the sentence says so ("about", "roughly", "nearly" ...)
        hedged = bool(HEDGE.search(before))
        if matches(own, x, dec, loose=hedged): ok_vals.append(abs(x)); continue
        # a figure from another part of the facts (an earlier lesson's result): only as an exact rounding of a
        # number with at least three significant digits, which is unlikely to match by chance
        if len(re.sub(r"\D", "", tok).lstrip("0")) >= 3 and matches(ALL, x, dec, loose=False): ok_vals.append(abs(x)); elsewhere.append(tok); continue
        out.append([where, tok, x, dec, ctx])
    # arithmetic on figures quoted in the same lesson: a difference, a sum, a ratio, a share, a product
    vals = sorted(v for v in set(ok_vals) if v > 0)     # only figures already traced to the facts may be combined
    derived, bad = [], []
    for where, tok, x, dec, ctx in out:
        ax, unit = abs(x), 10 ** (-dec) * 0.6
        if dec == 0 and ax >= 100 and ax % 10 == 0: unit = max(unit, ax * 0.02)
        hit = None
        for i, a in enumerate(vals):
            for b in vals[i + 1:]:
                for label, r in (("-", b - a), ("+", a + b), ("/", b / a), ("% of", 100 * a / b), ("% change", 100 * (b - a) / a), ("% change", 100 * (b - a) / b)):
                    if abs(r - ax) <= unit: hit = f"{b:g} {label} {a:g}"; break
                if hit: break
            if hit: break
        (derived if hit else bad).append({"where": where, "number": tok, "context": ctx, **({"from": hit} if hit else {})})
    return {"checked": len(found), "keys": sorted(EVID.get(les["id"], [])), "elsewhere": sorted(set(elsewhere)), "derived": derived, "unverified": bad}

only = sys.argv[1] if len(sys.argv) > 1 else None
report, tot = {}, [0, 0, 0]
for f in sorted((ROOT / "content/lessons").glob("*.json")):
    les = json.loads(f.read_text(encoding="utf-8"))
    if only and les["id"] != only: continue
    r = lint(les); report[les["id"]] = r
    tot[0] += r["checked"]; tot[1] += len(r["derived"]); tot[2] += len(r["unverified"])
(ROOT / "qa").mkdir(exist_ok=True)
(ROOT / "qa/numbers_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
for lid, r in report.items():
    if r["unverified"] or r["derived"]:
        print(f"\n{lid}: {len(r['unverified'])} unverified, {len(r['derived'])} derived, {r['checked']} numbers   keys: {', '.join(r['keys'])}")
        for u in r["unverified"]: print(f"   ?? {u['number']:>9}  [{u['where']}]  ...{u['context']}...")
        for u in r["derived"]: print(f"   =  {u['number']:>9}  [{u['where']}]  = {u['from']}   ...{u['context'][:70]}...")
print(f"\n{tot[0]} numbers read, {tot[1]} traced to arithmetic on quoted figures, {tot[2]} unverified, in {len(report)} lessons")
sys.exit(1 if tot[2] else 0)
