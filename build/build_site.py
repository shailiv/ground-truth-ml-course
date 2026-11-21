"""Assemble the site's data from the lesson files.
  content/lessons/*.json + content/site.json + content/practice.json + data/audio_manifest.json
    -> site/public/data/course.json, site/public/data/assistant-pack.md
Usage: python build/build_site.py [--allow-missing]
"""
import glob
import json
import pathlib
import re
import sys

sys.path.insert(0, "build")
from validate import check  # noqa: E402
from narration import text_key, drill_text_key  # noqa: E402

ROOT = pathlib.Path(".")
site = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
practice = []                         # case files and labs are authored in separate files and merged here
for name in ("practice_cases.json", "practice_labs.json", "practice.json"):
    pr_path = ROOT / "content" / name
    if pr_path.exists(): practice += json.loads(pr_path.read_text(encoding="utf-8"))
practice.sort(key=lambda p: (p["after"], p["kind"] != "lab", p["id"]))
man_path = ROOT / "data/audio_manifest.json"
manifest = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}

lessons, problems, stale_audio = [], 0, []
for f in sorted(glob.glob("content/lessons/*.json")):
    errs, warn, total = check(f)
    if errs:
        problems += 1
        print(f"FAIL {f}: {errs[0]}")
        continue
    L = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
    aud = manifest.get("lessons", {}).get(L["id"], [])
    # a clip is only good for the exact words it was recorded from: an edited sentence makes its clip stale
    fresh = len(aud) == len(L["segments"]) and all(a.get("src") and a.get("text") == text_key(sg["narration"]) for a, sg in zip(aud, L["segments"]))
    if aud and not fresh:
        stale_audio.append(L["id"] + ":" + ",".join(str(i + 1) for i, sg in enumerate(L["segments"]) if i >= len(aud) or aud[i].get("text") != text_key(sg["narration"])))
    L["audio"] = [{"src": a["src"], "dur": a["dur"]} for a in aud] if fresh else None
    L["minutes"] = round(sum(a["dur"] for a in aud) / 60, 1) if L["audio"] else round(total / 150, 1)
    L["words"] = total
    lessons.append(L)
lessons.sort(key=lambda l: tuple(int(x) for x in l["id"].split("-")))
ids = [l["id"] for l in lessons]
expected = 37
if len(lessons) != expected and "--allow-missing" not in sys.argv:
    print(f"only {len(lessons)} of {expected} lessons are valid; pass --allow-missing to build anyway")
    sys.exit(1)

seen, glossary = set(), []
for l in lessons:
    for g in l["glossary"]:
        k = g["term"].strip().lower()
        if k not in seen:
            seen.add(k)
            glossary.append({"term": g["term"], "def": g["def"], "lesson": l["id"]})
glossary.sort(key=lambda g: g["term"].lower())

drills = {}
for m in site["modules"]:
    items = [d for l in lessons if l["module"] == m["n"] for d in l["drill"]]
    d = manifest.get("drills", {}).get(str(m["n"]))
    if d and d.get("text") != drill_text_key(m["n"], items, m["title"]):
        stale_audio.append(f"drill-{m['n']}"); d = None                # a question or answer changed since the track was recorded
    drills[m["n"]] = {"items": items, "src": d["src"] if d else None, "dur": d["dur"] if d else None}

# ---- numbers the About page quotes about how the course was checked: read from the review records, never typed
def review_stats():
    q = ROOT / "qa"
    st = {}
    def load(name, default):
        f = q / name
        try: return json.loads(f.read_text(encoding="utf-8"))
        except Exception: return default
    key = load("planted_key.json", [])
    st["planted"], st["planted_numbers"], st["planted_concepts"] = len(key), sum(k["type"] == "number" for k in key), sum(k["type"] == "concept" for k in key)
    sc = load("review_scores.json", {})
    ex = [v for k, v in sc.items() if k.startswith("expert")]
    st["expert_planted"], st["expert_caught"] = sum(v["planted"] for v in ex), sum(v["caught"] for v in ex)
    g = sc.get("gemini", {})
    st["gemini_planted"], st["gemini_caught"], st["gemini_lessons"] = g.get("planted", 0), g.get("caught", 0), g.get("lessons", 0)
    st["real_findings"] = len(load("findings_real.json", []))
    dec = {}
    for f in sorted((q / "adjudication").glob("*.decisions.json")):
        for d in load("adjudication/" + f.name, {}).get("decisions", []):
            k = str(d.get("decision", "")).strip().lower().replace(" ", "_")
            dec[k] = dec.get(k, 0) + 1
    st["accepted"], st["partly"], st["rejected"] = dec.get("accepted", 0), dec.get("partly", 0), dec.get("rejected", 0)
    st["not_applicable"], st["out_of_scope"] = dec.get("not_applicable", 0), dec.get("out_of_scope", 0)
    st["adjudicated"] = sum(dec.values())
    fin = [load("factcheck/final/" + f.name, {}) for f in sorted((q / "factcheck/final").glob("*.json"))] if (q / "factcheck/final").exists() else []
    st["final_lessons"], st["final_issues"] = len(fin), sum(len(x.get("issues", [])) for x in fin)
    st["final_clean"] = sum(1 for x in fin if not x.get("issues"))
    # the second round: what the editors did with the final re-check's points, and the textbook terms they named
    r2 = {"accepted": 0, "partly": 0, "rejected": 0}; terms = 0; r2_lessons = 0
    for f in sorted((q / "adjudication").glob("*.round2.json")):
        d = load("adjudication/" + f.name, {}); r2_lessons += 1
        terms += sum(1 for t in d.get("terms", []) if t.get("glossary") or t.get("spoken"))
        for x in d.get("recheck", []):
            k = str(x.get("decision", "")).strip().lower()
            k = "accepted" if k.startswith(("accept", "already")) else "partly" if k.startswith("part") else "rejected" if k.startswith("reject") else None
            if k: r2[k] += 1
    st["r2_lessons"], st["r2_accepted"], st["r2_partly"], st["r2_rejected"], st["r2_terms"] = r2_lessons, r2["accepted"], r2["partly"], r2["rejected"], terms
    st["r2_points"] = sum(r2.values())
    ux = load("ux/report.json", {})
    st["ux_findings"] = len(ux.get("findings", []))
    st["code_findings"] = len(load("site_review_code.json", {}).get("findings", [])) + len(load("site_review_round2.json", {}).get("findings", []))
    # the check of the second round's own edits (build/factcheck_diff.py)
    r3 = [load("factcheck/round2_diff/" + f.name, {}) for f in sorted((q / "factcheck/round2_diff").glob("*.json"))] if (q / "factcheck/round2_diff").exists() else []
    st["r3_fields"], st["r3_problems"] = sum(x.get("_fields", 0) for x in r3), sum(len(x.get("problems", [])) for x in r3)
    st["site_tests"] = load("site_tests.json", {}).get("passed", 0)
    au = load("audio_report.json", {})
    st["clips"], st["audio_diff"], st["audio_flagged"] = au.get("clips", 0), round(100 * au.get("mean_wer", 0), 1), len(au.get("flagged", []))
    extra = load("review_notes.json", {})          # measurements made by hand during the build (linter mutation test, design scores, rounds)
    st.update(extra)
    return st

class _Missing(dict):
    def __missing__(self, k): raise SystemExit(f"About page asks for a number that no review record provides: {{{k}}}")
STATS = _Missing(review_stats())
site["about"] = [{"h": s_["h"], "p": [t.format_map(STATS) for t in s_["p"]]} for s_ in site["about"]]

# a facts box for the About page, computed here so it can never drift from what was actually built
audio_min = round(sum(a["dur"] for l in lessons for a in (l.get("audio") or [])) / 60)
questions = sum(1 + len(l["quiz"]) + sum(len(c["variants"]) for c in l["review"]) for l in lessons)
colophon = [["Lessons", f"{len(lessons)} in {len(site['modules'])} modules"], ["Narration", f"{audio_min} minutes, {sum(len(l['segments']) for l in lessons)} clips"],
            ["Questions", f"{questions:,}, plus {len(site['triage'])} triage cards"], ["Practice", f"{sum(p['kind'] == 'case' for p in practice)} case files, {sum(p['kind'] == 'lab' for p in practice)} labs"],
            ["Glossary", f"{len(glossary)} terms"], ["Voice", f"{manifest.get('voice', 'synthetic')} (synthetic)"]]

course = {"title": site["title"], "modules": site["modules"], "path": site["path"], "about": site["about"], "triage": site["triage"], "colophon": colophon,
          "lessons": lessons, "practice": practice, "glossary": glossary, "drills": drills,
          "total_minutes": round(sum(l["minutes"] for l in lessons)), "has_audio": sum(1 for l in lessons if l["audio"])}
out = ROOT / "site/public/data"
out.mkdir(parents=True, exist_ok=True)
(out / "course.json").write_text(json.dumps(course, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

# ---- the assistant pack: one file of standing instructions and audit checks
pack = ["# Standing instructions for my AI coding assistant",
        "",
        "I am a data analyst. When I ask you for modelling or analysis work, follow this file.",
        "",
        "## How we work",
        "1. Work in stages and stop at each gate for me to check: (1) the table, (2) the target and the split, (3) baseline then model, (4) the report.",
        "2. Every output carries an audit block: row counts and distinct entities after every step; date ranges; the label rate; every feature with its source table and the latest date of data it used; the baseline beside the model; training and test scores side by side; group sizes and intervals beside every comparison.",
        "3. Numbers in any report text are produced from the computed results, never typed. State what the reader should not conclude.",
        "4. Say which claims are observed, adjusted or tested. Do not write causal language over an association.",
        "5. If a result looks too good, say so yourself and show the result without the strongest column.",
        "6. Never drop rows, fill missing values or join tables silently: report what changed.",
        "",
        "## The path for any new question", ""]
pack += [f"{i + 1}. {t}" for i, t in enumerate(site["path"])]
# the one-page core: the standing instruction to pin; the full pack adds every lesson's brief and checks
import datetime
stamp = f"Version {datetime.date.today().isoformat()}, from the Ground Truth course."
(out / "assistant-core.md").write_text("\n".join(pack + ["", stamp, ""]), encoding="utf-8")
pack += ["", "# Reference: the brief and the checks for each kind of question", "", "Complete from day one: it covers every lesson of the course, including ones I may not have studied yet.", stamp]
for m in site["modules"]:
    pack += ["", f"## Module {m['n']}: {m['title']}", ""]
    for l in [x for x in lessons if x["module"] == m["n"]]:
        pack += [f"### {l['title']}", "", "Brief:", "", l["ask_assistant"], "", "The output must show:", ""] + [f"- {c}" for c in l["audit_checklist"]] + [""]
(out / "assistant-pack.md").write_text("\n".join(pack), encoding="utf-8")

words = sum(l["words"] for l in lessons)
print(f"course.json: {len(lessons)} lessons ({problems} failed validation), {words:,} narration words, about {course['total_minutes']} min, "
      f"{course['has_audio']} with audio, {len(glossary)} glossary terms, {len(practice)} practice files, {len(site['triage'])} triage cards")
missing = [f"{m}-{k}" for m, n in ((1, 5), (2, 6), (3, 5), (4, 6), (5, 6), (6, 4), (7, 5)) for k in range(1, n + 1) if f"{m}-{k}" not in ids]
if missing:
    print("missing:", " ".join(missing))

# ---- audio: a lesson without narration must stop a real build; clips nothing points to must not be published
silent = [l["id"] for l in lessons if not l["audio"]]
no_drill = [str(n) for n, d in drills.items() if not d["src"]]
if stale_audio:
    print("audio recorded from older text (lesson:parts), re-record with build/tts.py:", " ".join(stale_audio))
if silent or no_drill:
    print(f"no audio: lessons {' '.join(silent) or '-'}; drills {' '.join(no_drill) or '-'}")
    if "--allow-missing" not in sys.argv:
        sys.exit(1)
used = {a["src"] for l in lessons for a in (l["audio"] or [])} | {d["src"] for d in drills.values() if d["src"]}
stale = [f for f in (ROOT / "site/public/audio").rglob("*.mp3") if f.relative_to(ROOT / "site/public").as_posix() not in used]
if stale:
    print(f"{len(stale)} audio clips are no longer used by any lesson" + ("" if "--prune" in sys.argv else " (run with --prune to delete them)"))
    if "--prune" in sys.argv:
        for f in stale: f.unlink()
