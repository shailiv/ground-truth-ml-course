"""Listen back to every narration clip: transcribe it with a speech-to-text model and compare with the script.

  python build/tts_verify.py [ids...]      -> qa/audio_report.json, exit 1 if any clip needs a human ear

A clip is flagged when (a) a number in the script is missing from, or different in, what was heard, or
(b) more than 7% of the words differ after normalising spelling, contractions and number words, or
(c) it is implausibly short or long for its word count (a cut-off or a stall).
Transcripts are cached per clip, so a re-run only listens to new audio.
"""
import concurrent.futures as cf, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/gemini/scripts"))
import gemini as G
sys.path.insert(0, str(ROOT / "build"))
from tts import spoken

CACHE = ROOT / "data/audio_transcripts"; CACHE.mkdir(parents=True, exist_ok=True)
MODEL = G.resolve("transcribe", "transcribe")
from speechnorm import words      # one spelling for script and transcript

def wer(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1] / max(1, len(a))

def hear(mp3):
    c = CACHE / (mp3.stem + ".txt")
    if c.exists(): return c.read_text(encoding="utf-8")
    part = G.file_part(str(mp3))
    body = {"model": MODEL, "input": [{"type": "user_input", "content": [part]}], "generation_config": {"transcription_config": {"language_codes": ["en-US"]}}}
    for attempt in range(3):
        try:
            d = G.http("POST", "interactions", body, timeout=600)
            text = " ".join(c2.get("text", "") for st in d.get("steps", []) or [] for c2 in st.get("content") or [] if c2.get("type") == "text").strip()
            if text: c.write_text(text, encoding="utf-8"); return text
        except SystemExit: pass
        except Exception: pass
    return ""

def main():
    man = json.loads((ROOT / "data/audio_manifest.json").read_text(encoding="utf-8"))
    only = set(sys.argv[1:])
    jobs = []
    for f in sorted((ROOT / "content/lessons").glob("*.json")):
        les = json.loads(f.read_text(encoding="utf-8"))
        if only and les["id"] not in only: continue
        for i, (seg, rec) in enumerate(zip(les["segments"], man["lessons"].get(les["id"], []))):
            jobs.append((les["id"], i + 1, spoken(seg["narration"]), ROOT / "site/public" / rec["src"], rec["dur"]))
    def one(j):
        lid, n, script, mp3, dur = j
        heard = hear(mp3)
        a, b = words(script), words(heard)
        nums_a, nums_b = sorted(w for w in a if re.search(r"\d", w)), sorted(w for w in b if re.search(r"\d", w))
        missing = [x for x in set(nums_a) if nums_a.count(x) > nums_b.count(x)]
        extra = [x for x in set(nums_b) if nums_b.count(x) > nums_a.count(x)]
        rate = len(a) / dur * 60 if dur else 0
        e = wer(a, b)
        why = []
        if not heard: why.append("no transcript")
        if missing or extra: why.append(f"numbers differ: script has {missing}, heard {extra}")
        if e > 0.07: why.append(f"{e:.0%} of words differ")
        if rate and not 115 <= rate <= 215: why.append(f"{rate:.0f} words a minute")
        return {"lesson": lid, "seg": n, "wer": round(e, 3), "wpm": round(rate), "flags": why, "script": script, "heard": heard, "file": str(mp3.name)}
    with cf.ThreadPoolExecutor(6) as ex: rows = list(ex.map(one, jobs))
    bad = [r for r in rows if r["flags"]]
    (ROOT / "qa/audio_report.json").write_text(json.dumps({"clips": len(rows), "flagged": bad, "mean_wer": round(sum(r["wer"] for r in rows) / max(1, len(rows)), 4),
                                                         "all": [{k: r[k] for k in ("lesson", "seg", "wer", "wpm")} for r in rows]}, indent=1, ensure_ascii=False), encoding="utf-8")
    for r in bad: print(f"{r['lesson']} seg{r['seg']}: {'; '.join(r['flags'])}")
    print(f"{len(rows)} clips heard back, mean word difference {100 * sum(r['wer'] for r in rows) / max(1, len(rows)):.1f}%, {len(bad)} flagged")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
