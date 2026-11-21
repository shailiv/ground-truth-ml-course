"""Independent fact-check of every lesson by a Gemini model, with the computed facts attached.

  python build/factcheck.py [--dir qa/blind/lessons] [--out qa/factcheck/gemini] [--model smart] [ids...]

One call per lesson: the model gets data/facts.json (the only source of truth for numbers), the lesson's brief
from the outline (what it may assume was taught before), and the lesson itself. It returns a JSON list of issues.
Results are cached per lesson by content hash, so a re-run only re-checks lessons that changed.
"""
import argparse, concurrent.futures as cf, hashlib, json, pathlib, re, subprocess, sys, tempfile, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
G = pathlib.Path.home() / ".claude/skills/gemini/scripts/gemini.py"
ap = argparse.ArgumentParser()
ap.add_argument("ids", nargs="*")
ap.add_argument("--dir", default="qa/blind/lessons")
ap.add_argument("--out", default="qa/factcheck/gemini")
ap.add_argument("--model", default="smart")
ap.add_argument("--workers", type=int, default=4)
ap.add_argument("--thinking", default="high")
a = ap.parse_args()
SRC, OUT = ROOT / a.dir, ROOT / a.out
OUT.mkdir(parents=True, exist_ok=True)
OUTLINE = (ROOT / "content/OUTLINE.md").read_text(encoding="utf-8")

SYSTEM = """You are a senior machine-learning practitioner acting as an adversarial fact-checker for a course.
You are given three things:
1. FACTS: facts.json - the complete computed results of the course's simulated data. It is the ONLY source of truth for
   any number about that data. Models, splits and row counts are described inside it.
2. BRIEF: the lesson's brief from the course outline (what it should teach and what earlier lessons already taught).
3. LESSON: one lesson as JSON - narrated segments (text-to-speech narration plus one visual each), a guess question,
   quiz questions, spaced-review questions, audio drill items, an explain-back prompt, an assistant brief, an audit
   checklist, transfer examples, alternatives and a glossary.

Find every real problem. Check each numeric claim against FACTS one by one - do not skim. Report:
- number_mismatch: a figure, comparison, direction or count that contradicts FACTS, or is attached to the wrong thing
  (wrong model, wrong cut-off, wrong rows, train vs test, wrong unit).
- unsupported_number: a figure stated about the simulated data that is not in FACTS and cannot be derived from FACTS by
  simple arithmetic.
- wrong_concept: a statement about machine learning, statistics or causal inference that is false.
- misleading: true only with a caveat the lesson leaves out, in a way that would lead a practitioner to a wrong decision,
  or a result of this one simulation presented as a general law.
- bad_question: a quiz/review/guess item whose keyed answer is wrong, where a second option is equally defensible, or
  whose explanation contradicts the lesson. ("answer" is the 0-based index into "options".)
- contradiction: the narration and its visual, or two parts of the lesson, disagree.

Do NOT report: style or wording preferences; honest rounding for speech ("about 0.85" for 0.845, "roughly one in five"
for 19.7%); numbers inside a clearly labelled toy example ("say you have 1,000..."); invented numbers in questions set
in a different domain (domain "other", review variants, transfer examples) - but DO check that the reasoning in those
questions is correct. Do not pad the list: if a part is right, say nothing about it.

For each issue give: where (e.g. "seg3 narration", "seg5 visual", "quiz 2-2-q3", "review 1 variant 2", "glossary"),
quote (the exact words or number at fault, short), kind, severity (high = teaches something false or states a wrong
number; medium = likely to mislead; low = minor), explanation (what is wrong), evidence (the facts.json path and value,
or the principle), and fix (a concrete corrected wording or number)."""

SCHEMA = {"type": "object", "properties": {
    "issues": {"type": "array", "items": {"type": "object", "properties": {
        "where": {"type": "string"}, "quote": {"type": "string"},
        "kind": {"type": "string", "enum": ["number_mismatch", "unsupported_number", "wrong_concept", "misleading", "bad_question", "contradiction"]},
        "severity": {"type": "string", "enum": ["high", "medium", "low"]},
        "explanation": {"type": "string"}, "evidence": {"type": "string"}, "fix": {"type": "string"}},
        "required": ["where", "quote", "kind", "severity", "explanation", "evidence", "fix"]}},
    "numbers_checked": {"type": "integer"}, "verdict": {"type": "string"}},
    "required": ["issues", "numbers_checked", "verdict"]}

def brief(lid):
    m = re.search(r"^### " + re.escape(lid) + r" .*?(?=^### |^## |\Z)", OUTLINE, re.S | re.M)
    return m.group(0) if m else ""

def check(path):
    lid = path.stem
    text = path.read_text(encoding="utf-8")
    h = hashlib.sha256((text + SYSTEM + a.model).encode()).hexdigest()[:16]
    dest = OUT / f"{lid}.json"
    if dest.exists():
        try:
            old = json.loads(dest.read_text(encoding="utf-8"))
            if old.get("_hash") == h: return lid, len(old["issues"]), "cached"
        except Exception: pass
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        (td / "LESSON.json").write_text(text, encoding="utf-8")
        (td / "BRIEF.md").write_text(brief(lid) or "(no brief found)", encoding="utf-8")
        (td / "schema.json").write_text(json.dumps(SCHEMA), encoding="utf-8")
        (td / "system.txt").write_text(SYSTEM, encoding="utf-8")
        cmd = [sys.executable, str(G), "ask", "-m", a.model, "--thinking", a.thinking, "--max-tokens", "40000", "-s", "@" + str(td / "system.txt"),
               "-f", str(ROOT / "data/facts.json"), "-f", str(td / "BRIEF.md"), "-f", str(td / "LESSON.json"),
               "--json-schema", str(td / "schema.json"),
               f"Fact-check lesson {lid}. The three attached files are FACTS (facts.json), BRIEF (BRIEF.md) and LESSON (LESSON.json). Return the JSON."]
        level = a.thinking
        for attempt in range(3):
            cmd[cmd.index("--thinking") + 1] = level
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            # the model sometimes pauses mid-answer at the highest setting ("requires_continuation"): asking again the
            # same way pauses again, so step the thinking down instead of paying for the same failure twice
            if "requires_continuation" in (r.stderr or ""): level = {"high": "medium", "medium": "low"}.get(level, "low")
            try:
                out = json.loads(r.stdout)
                out["_hash"] = h; out["_thinking"] = level; out["_status"] = (r.stderr.strip().splitlines() or [""])[-1][:200]
                dest.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
                return lid, len(out["issues"]), out["_status"]
            except Exception as e:
                err = f"{type(e).__name__}: {(r.stderr or '')[-300:]}"
        return lid, -1, err

files = sorted(p for p in SRC.glob("*.json") if not a.ids or p.stem in a.ids)
with cf.ThreadPoolExecutor(a.workers) as ex:
    for lid, n, status in ex.map(check, files):
        print(f"{lid}: {n} issues  [{status}]", flush=True)
