"""Show which segments' narration changed since the last commit, with the old and new text side by side.
    python build/narration_diff.py [ids...]          (default: every lesson)
    python build/narration_diff.py --list            (just lesson:parts, for the re-recording list)
Used before re-recording: every changed clip costs money, so each change is read first.
"""
import difflib, json, pathlib, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")
from narration import spoken

args = [a for a in sys.argv[1:] if not a.startswith("--")]
brief = "--list" in sys.argv
total = 0
for f in sorted(pathlib.Path("content/lessons").glob("*.json")):
    if args and f.stem not in args:
        continue
    new = json.loads(f.read_text(encoding="utf-8"))
    r = subprocess.run(["git", "show", f"HEAD:content/lessons/{f.name}"], capture_output=True, text=True, encoding="utf-8")
    old = json.loads(r.stdout) if r.returncode == 0 else {"segments": []}
    changed = []
    for i, sg in enumerate(new["segments"]):
        before = spoken(old["segments"][i]["narration"]) if i < len(old["segments"]) else ""
        after = spoken(sg["narration"])
        if before != after:
            changed.append((i, before, after))
    if not changed:
        continue
    total += len(changed)
    if brief:
        print(f"{f.stem}: parts {', '.join(str(i + 1) for i, _, _ in changed)}")
        continue
    for i, before, after in changed:
        print(f"=== {f.stem} part {i + 1}  ({len(after.split())} words, was {len(before.split())})")
        a, b = before.split(), after.split()
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            ctx = " ".join(a[max(0, i1 - 6):i1])
            print(f"   ...{ctx} [-{' '.join(a[i1:i2])}-] {{+{' '.join(b[j1:j2])}+}}")
print(f"{total} clips to re-record")
