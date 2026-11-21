"""Validate lesson JSON files against content/SPEC.md (v3). Usage: python build/validate.py [files...]"""
import glob
import json
import re
import sys

VIS = {
    "title": {"kicker", "title", "sub"}, "bullets": {"title", "items"}, "quote": {"text"},
    "compare": {"title", "left", "right"}, "stat": {"title", "stats"}, "table": {"title", "columns", "rows"},
    "bar": {"title", "data"}, "line": {"title", "x", "series"}, "matrix": {"title", "tp", "fp", "fn", "tn"},
    "flow": {"title", "steps"}, "timeline": {"title", "spans"}, "code": {"title", "lang", "code"},
    "widget": {"name", "title"}, "formula": {"title", "lines"},
}
WIDGETS = {"threshold", "depth", "tree", "practices", "calibration", "ranklist", "forecast", "anomalies", "ticket_map", "survival"}
CUE_ITEMS = {"bullets": "items", "flow": "steps", "stat": "stats", "formula": "lines", "table": "rows", "bar": "data", "timeline": "spans"}
BAD_AUDIO = [r"as you can see", r"on the (left|right)", r"\bthis (chart|table|slide|picture|graph)\b", r"shown (here|above|below)",
             r"\bthe (red|green|blue|orange|grey|gray) (bar|line|box|dot)", r"[*`#]", r"\(|\)", r"\be\.g\.", r"\bi\.e\.", r"%", r"\w_\w", r"\bsklearn\b", r"\bROAS\b"]
TOP = ["id", "module", "title", "subtitle", "goal", "predict", "segments", "takeaways", "quiz", "review", "drill", "recall",
       "ask_assistant", "audit_checklist", "transfer", "other_ways", "glossary"]
NUM = re.compile(r"(?<![A-Za-z])\$?\d[\d,]*(?:\.\d+)?")


def words(s):
    return len(re.findall(r"[A-Za-z0-9']+", s))


def mcq(x, where, errs, warn, need_id=None):
    if not {"q", "options", "answer", "why"} <= set(x):
        errs.append(f"{where}: needs q, options, answer, why")
        return
    if len(x["options"]) != 4 or not isinstance(x["answer"], int) or not 0 <= x["answer"] <= 3:
        errs.append(f"{where}: need 4 options and a 0-3 answer")
        return
    if need_id and x.get("id") != need_id:
        errs.append(f"{where}: id must be {need_id}")
    lens = [len(o) for o in x["options"]]
    if lens[x["answer"]] == max(lens) and lens[x["answer"]] > 1.7 * sorted(lens)[-2]:
        warn.append(f"{where}: the right answer is much longer than the others (a giveaway)")
    if len(set(o.strip().lower() for o in x["options"])) < 4:
        errs.append(f"{where}: duplicate options")
    if words(x["why"]) < 8:
        warn.append(f"{where}: 'why' is too thin to teach anything")


def check(path):
    errs, warn = [], []
    try:
        L = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"not valid JSON: {e}"], [], 0
    for k in TOP:
        if k not in L:
            errs.append(f"missing key '{k}'")
    if errs:
        return errs, warn, 0
    if not re.fullmatch(r"\d-\d", L["id"]) or not path.replace("\\", "/").endswith(f"/{L['id']}.json"):
        errs.append("id must look like '3-1' and match the file name")
    if words(L["title"]) > 7:
        warn.append("title is long (max 6 words)")
    segs = L["segments"]
    if not 6 <= len(segs) <= 9:
        errs.append(f"{len(segs)} segments (want 6-9)")
    total = 0
    for i, s in enumerate(segs):
        raw = s.get("narration", "")
        cues = [int(c) for c in re.findall(r"\[\[(\d+)\]\]", raw)]
        spoken = re.sub(r"\s*\[\[\d+\]\]\s*", " ", raw).strip()
        if re.search(r"\[\[|\]\]", spoken):
            errs.append(f"segment {i + 1}: malformed cue marker (use [[1]], [[2]] ...)")
        if cues != sorted(set(cues)):
            errs.append(f"segment {i + 1}: cue markers must be ascending and unique")
        n = words(spoken)
        total += n
        if n < 40 or n > 140:
            (errs if n > 160 or n < 25 else warn).append(f"segment {i + 1}: {n} words (want 50-130)")
        for pat in BAD_AUDIO:
            m = re.search(pat, spoken, re.I)
            if m:
                errs.append(f"segment {i + 1} narration: not ear-friendly: '{m.group(0)}'")
        for sent in re.split(r"(?<=[.!?])\s+", spoken):
            nums = NUM.findall(sent)
            if len(nums) > 3:
                errs.append(f"segment {i + 1}: {len(nums)} numbers in one sentence (max 2, put the table on screen): \"{sent[:70]}...\"")
            elif len(nums) == 3:
                warn.append(f"segment {i + 1}: 3 numbers in one sentence (aim for 2): \"{sent[:60]}...\"")
        v = s.get("visual") or {}
        t = v.get("type")
        if t not in VIS:
            errs.append(f"segment {i + 1}: unknown visual type {t!r}")
            continue
        miss = VIS[t] - set(v)
        if miss:
            errs.append(f"segment {i + 1} ({t}): missing {sorted(miss)}")
            continue
        n_items = 2 if t == "compare" else (len(v[CUE_ITEMS[t]]) if t in CUE_ITEMS else 0)
        if cues and (not n_items or max(cues) > n_items or min(cues) < 1):
            errs.append(f"segment {i + 1}: cue markers {cues} do not match the {n_items} items of a '{t}' visual")
        if i == 0 and t != "title":
            errs.append("first segment's visual must be type 'title'")
        if t == "widget" and v["name"] not in WIDGETS:
            errs.append(f"segment {i + 1}: unknown widget {v['name']!r}")
        if t == "formula" and not 1 <= len(v["lines"]) <= 4:
            errs.append(f"segment {i + 1}: formula needs 1-4 lines")
        if t == "bullets" and not 1 <= len(v["items"]) <= 5:
            errs.append(f"segment {i + 1}: bullets needs 1-5 items")
        if t == "stat" and not 1 <= len(v["stats"]) <= 4:
            errs.append(f"segment {i + 1}: stat needs 1-4 stats")
        if t == "flow" and not 2 <= len(v["steps"]) <= 6:
            errs.append(f"segment {i + 1}: flow needs 2-6 steps")
        if t == "table":
            if len(v["columns"]) > 6 or len(v["rows"]) > 7:
                errs.append(f"segment {i + 1}: table too big (max 6 cols x 7 rows)")
            if any(len(r) != len(v["columns"]) for r in v["rows"]):
                errs.append(f"segment {i + 1}: table rows must match the column count")
            if any(not isinstance(c, str) for r in v["rows"] for c in r):
                errs.append(f"segment {i + 1}: table cells must all be strings")
        if t == "bar":
            if not 2 <= len(v["data"]) <= 8 or any(not isinstance(d.get("value"), (int, float)) for d in v["data"]):
                errs.append(f"segment {i + 1}: bar needs 2-8 items with numeric 'value'")
            if v.get("unit") not in (None, "%", "$", "pts", ""):
                errs.append(f"segment {i + 1}: bar unit must be %, $, pts or omitted")
        if t == "line":
            if not 1 <= len(v["series"]) <= 3 or any(len(s_["values"]) != len(v["x"]) for s_ in v["series"]) or len(v["x"]) > 30:
                errs.append(f"segment {i + 1}: line needs 1-3 series, each with len(x) values, at most 30 points")
        if t == "matrix" and any(not isinstance(v[k], int) for k in ("tp", "fp", "fn", "tn")):
            errs.append(f"segment {i + 1}: matrix counts must be integers")
        if t == "timeline" and any(sp.get("kind") not in ("obs", "out", "bad", "ok") or not isinstance(sp.get("from"), (int, float)) or not isinstance(sp.get("to"), (int, float)) for sp in v["spans"]):
            errs.append(f"segment {i + 1}: timeline spans need numeric from/to and kind obs|out|bad|ok")
        if t == "code":
            if v["lang"] not in ("python", "sql", "text"):
                errs.append(f"segment {i + 1}: code lang must be python|sql|text")
            lines = v["code"].split("\n")
            if len(lines) > 14 or any(len(x) > 74 for x in lines):
                errs.append(f"segment {i + 1}: code too long (max 12 lines of 70 chars)")
        if t == "compare" and any(not {"label", "value"} <= set(v[s_]) for s_ in ("left", "right")):
            errs.append(f"segment {i + 1}: compare sides need label and value")
        vis_words = words(json.dumps({k: x for k, x in v.items() if k not in ("type", "code", "rows", "x", "series", "data")}))
        if vis_words > 75:
            warn.append(f"segment {i + 1}: visual text is {vis_words} words (aim under 40)")
    if total > 950:
        errs.append(f"{total} narration words (hard cap 950)")
    elif total < 620:
        warn.append(f"{total} narration words (aim 650-900)")
    q = L["quiz"]
    if len(q) != 4:
        errs.append(f"{len(q)} quiz questions (need exactly 4)")
    for i, x in enumerate(q):
        mcq(x, f"quiz {i + 1}", errs, warn, f"{L['id']}-q{i + 1}")
        if x.get("domain") not in ("course", "other"):
            errs.append(f"quiz {i + 1}: domain must be 'course' or 'other'")
        if not x.get("concept"):
            errs.append(f"quiz {i + 1}: missing concept")
    if not any(x.get("domain") == "other" for x in q):
        errs.append("quiz: at least one question must have domain 'other' (a different problem from the lesson's example)")
    if len({x.get("answer") for x in q}) < 3:
        warn.append("quiz: vary the position of the correct answer more")
    rv = L["review"]
    if len(rv) != 2:
        errs.append(f"review needs exactly 2 concepts (has {len(rv)})")
    for i, c in enumerate(rv):
        if not c.get("concept") or len(c.get("variants", [])) != 3:
            errs.append(f"review {i + 1}: needs a concept and exactly 3 variants")
            continue
        for j, x in enumerate(c["variants"]):
            mcq(x, f"review {i + 1} variant {j + 1}", errs, warn)
        if len({x.get("answer") for x in c["variants"]}) < 2:
            warn.append(f"review {i + 1}: all three variants have the right answer in the same position")
    # a pattern a learner picks up within a lesson or two: "the longest option is the right one"
    allq = [x for x in q if isinstance(x.get("answer"), int) and len(x.get("options", [])) == 4] + \
           [x for c in rv for x in c.get("variants", []) if isinstance(x.get("answer"), int) and len(x.get("options", [])) == 4]
    longest = sum(1 for x in allq if len(x["options"][x["answer"]]) == max(len(o) for o in x["options"]))
    if allq and longest > 0.4 * len(allq):
        errs.append(f"the right answer is the longest option in {longest} of {len(allq)} questions (chance is 1 in 4): "
                    "make distractors as long and as specific as the answer, or tighten the answer")
    dr = L["drill"]
    if len(dr) != 2 or any(not {"q", "a"} <= set(x) for x in dr):
        errs.append("drill needs exactly 2 items with q and a")
    else:
        for i, x in enumerate(dr):
            if re.search(r"[%()*_#]", x["q"] + x["a"]):
                errs.append(f"drill {i + 1}: write for the ear (no %, brackets or symbols)")
            if words(x["a"]) > 60:
                warn.append(f"drill {i + 1}: answer is long for audio")
    pr = L["predict"]
    if not {"q", "options", "answer", "reveal"} <= set(pr) or not 3 <= len(pr.get("options", [])) <= 4 or not isinstance(pr.get("answer"), int) or not 0 <= pr["answer"] < len(pr["options"]):
        errs.append("predict needs q, 3-4 options, a valid 0-based answer, and reveal")
    if len(L["takeaways"]) != 3:
        errs.append("need exactly 3 takeaways")
    if not {"prompt", "model_answer"} <= set(L["recall"]):
        errs.append("recall needs prompt and model_answer")
    if not 2 <= len(L["audit_checklist"]) <= 4:
        errs.append("audit_checklist needs 2-4 items")
    if len(L["transfer"]) != 3:
        errs.append("transfer needs exactly 3 items")
    if not 2 <= len(L["other_ways"]) <= 3 or any(not {"approach", "when"} <= set(x) for x in L["other_ways"]):
        errs.append("other_ways needs 2-3 items with approach and when")
    if not 2 <= len(L["glossary"]) <= 7 or any(not {"term", "def"} <= set(x) for x in L["glossary"]):
        errs.append("glossary needs 2-7 items with term and def")
    return errs, warn, total


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob("content/lessons/*.json"))
    bad = 0
    for f in files:
        errs, warn, total = check(f)
        bad += bool(errs)
        print(f"{'FAIL' if errs else 'ok  '} {f}  ({total} words)")
        for e in errs:
            print("   ERROR  " + e)
        for w in warn:
            print("   warn   " + w)
    sys.exit(1 if bad else 0)
