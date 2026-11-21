"""Fact-check only what an edit round changed.

After a correction round, re-reading whole lessons is expensive and unfocused. This sends a second model the
results file plus every changed field (old text and new text) and asks one question of each change: is the NEW
text right, against the facts and as a general statement about machine learning?

    python build/factcheck_diff.py --base <commit> [--out qa/factcheck/round2_diff] [--batch 8] [ids...]

Writes one JSON per batch into the out folder and prints the problems found.
"""
import argparse, json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
G = pathlib.Path.home() / ".claude/skills/gemini/scripts/gemini.py"
ap = argparse.ArgumentParser()
ap.add_argument("ids", nargs="*")
ap.add_argument("--base", required=True)
ap.add_argument("--out", default="qa/factcheck/round2_diff")
ap.add_argument("--batch", type=int, default=8)
ap.add_argument("--model", default="smart")
ap.add_argument("--thinking", default="medium")
a = ap.parse_args()
sys.stdout.reconfigure(encoding="utf-8")

SYSTEM = """You are a meticulous machine-learning reviewer checking the last round of edits to a course for a working data analyst.

You are given FACTS (facts.json: every number the course is allowed to quote, computed on simulated advertiser data; for the support-ticket lessons 7-1 to 7-5 also TICKET_FACTS) and CHANGES: for each lesson, the fields an editor changed, each with its path, the old text and the new text.

For every change, judge the NEW text only:
1. Every number, direction and comparison in it must agree with FACTS (rounding to the precision shown is fine; a number rounded in speech is fine).
2. Every statement about machine learning or statistics must be correct as a general principle, at the level of a careful introductory course. A deliberate simplification is acceptable; a false statement is not.
3. A newly introduced textbook term (for example supervised learning, lift, p-value, bias-variance trade-off, one-hot encoding, zero-shot) must be defined correctly.
4. The new text must not contradict the old text's surrounding claim in a way that looks accidental.

Report only real problems. Do not report style, tone or things you would merely phrase differently. If a number cannot be found in FACTS, say so and name the nearest key you looked at. Be specific: quote the wrong words and give the corrected words."""

SCHEMA = {"type": "object", "properties": {
    "changes_checked": {"type": "integer"},
    "problems": {"type": "array", "items": {"type": "object", "properties": {
        "lesson": {"type": "string"}, "path": {"type": "string"}, "severity": {"type": "string", "enum": ["high", "medium", "low"]},
        "wrong": {"type": "string"}, "why": {"type": "string"}, "fix": {"type": "string"}},
        "required": ["lesson", "path", "severity", "wrong", "why", "fix"]}}},
    "required": ["changes_checked", "problems"]}


def walk(old, new, path, out):
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            walk(old.get(k), new.get(k), f"{path}.{k}" if path else k, out)
    elif isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        for i, (x, y) in enumerate(zip(old, new)):
            walk(x, y, f"{path}[{i}]", out)
    elif old != new:
        out.append({"path": path, "old": old, "new": new})


changes, n = {}, 0
for f in sorted((ROOT / "content/lessons").glob("*.json")):
    if a.ids and f.stem not in a.ids:
        continue
    r = subprocess.run(["git", "show", f"{a.base}:content/lessons/{f.name}"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if r.returncode:
        continue
    diffs = []
    walk(json.loads(r.stdout), json.loads(f.read_text(encoding="utf-8")), "", diffs)
    if diffs:
        changes[f.stem] = diffs; n += len(diffs)
print(f"{n} changed fields in {len(changes)} lessons since {a.base}")
out = ROOT / a.out; out.mkdir(parents=True, exist_ok=True)
ids = list(changes)
problems = []
for b in range(0, len(ids), a.batch):
    group = ids[b:b + a.batch]
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        (td / "CHANGES.json").write_text(json.dumps({k: changes[k] for k in group}, ensure_ascii=False, indent=1), encoding="utf-8")
        (td / "schema.json").write_text(json.dumps(SCHEMA), encoding="utf-8")
        (td / "system.txt").write_text(SYSTEM, encoding="utf-8")
        cmd = [sys.executable, str(G), "ask", "-m", a.model, "--thinking", a.thinking, "--max-tokens", "40000", "-s", "@" + str(td / "system.txt"),
               "-f", str(ROOT / "data/facts.json")]
        if any(k.startswith("7-") for k in group):
            cmd += ["-f", str(ROOT / "data/tickets_facts.json")]
        cmd += ["-f", str(td / "CHANGES.json"), "--json-schema", str(td / "schema.json"),
                "Check the edits in CHANGES.json (lessons " + ", ".join(group) + ") against FACTS (facts.json" + (" and TICKET_FACTS, tickets_facts.json" if any(k.startswith("7-") for k in group) else "") + "). Return the JSON."]
        res, level = None, a.thinking
        for attempt in range(3):
            cmd[cmd.index("--thinking") + 1] = level
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            if "requires_continuation" in (r.stderr or ""):
                level = {"high": "medium", "medium": "low"}.get(level, "low")
            try:
                res = json.loads(r.stdout); break
            except ValueError:
                err = (r.stderr or "")[-300:]
        if res is None:
            print(f"batch {group}: FAILED {err}"); continue
        res["_lessons"] = group; res["_fields"] = sum(len(changes[k]) for k in group)
        (out / f"batch-{group[0]}_{group[-1]}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"batch {group[0]}..{group[-1]}: {res['_fields']} fields, {len(res['problems'])} problems", flush=True)
        problems += res["problems"]
for p in problems:
    print(f"[{p['severity']}] {p['lesson']} {p['path']}\n    wrong: {p['wrong'][:300]}\n    why:   {p['why'][:400]}\n    fix:   {p['fix'][:300]}")
print(f"{len(problems)} problems in {n} changed fields")
