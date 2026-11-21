"""Narration audio. One clip per lesson segment, one recall-drill track per module.

  python build/tts.py                  everything that is missing or whose words changed
  python build/tts.py 2-3 4-1          only these lessons
  python build/tts.py --sample         three short voice samples in qa/voices/ (to choose a voice)
  python build/tts.py --drills         only the drill tracks

Each clip is cached by a hash of (words, voice, style, model): changing a sentence re-records one clip, nothing else.
WAV from the speech model -> ffmpeg (trim edge silence, even loudness, mono MP3) -> site/public/audio/.
Writes data/audio_manifest.json = {"lessons": {id: [{src, dur}]}, "drills": {module: {src, dur}}}.
"""
import argparse, base64, concurrent.futures as cf, hashlib, json, pathlib, re, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/gemini/scripts"))
import gemini as G

CFG = json.loads((ROOT / "content/voice.json").read_text(encoding="utf-8")) if (ROOT / "content/voice.json").exists() else {}
VOICE = CFG.get("voice", "Charon")
STYLE = CFG.get("style", "A senior analyst talking a sharp colleague through an idea at their desk. Warm, direct, a little dry. "
                         "Natural conversational pace, clear diction, a short breath between sentences. Not a presenter, not an advert.")
MODEL = G.resolve(CFG.get("model", "tts"), "tts")
AUDIO, WAVS = ROOT / "site/public/audio", ROOT / "data/audio_wav"
AUDIO.mkdir(parents=True, exist_ok=True); WAVS.mkdir(parents=True, exist_ok=True)

from narration import spoken, text_key, drill_parts, drill_text_key      # shared with build_site.py

def key(text, voice=None, style=None):
    return hashlib.sha256(json.dumps([text, voice or VOICE, style or STYLE, MODEL]).encode()).hexdigest()[:14]

def synth(text, voice=None, style=None):
    """Return the path of a cached WAV for these words, recording it if needed."""
    wav = WAVS / f"{key(text, voice, style)}.wav"
    if wav.exists() and wav.stat().st_size > 2000: return wav
    body = {"model": MODEL, "input": [{"type": "user_input", "content": [{"type": "text", "text": text,
            "annotations": [{"type": "speech_metadata", "style": style or STYLE}]}]}],
            "response_format": {"type": "audio"}, "generation_config": {"speech_config": [{"voice": voice or VOICE}]}}
    last = None
    for attempt in range(4):
        try:
            d = G.http("POST", "interactions", body, timeout=600)
            for step in d.get("steps", []) or []:
                for c in step.get("content") or []:
                    if c.get("data"):
                        raw = base64.b64decode(c["data"])
                        if raw[:4] != b"RIFF": raw = G.wav_wrap(raw)
                        wav.write_bytes(raw); return wav
            last = f"no audio in response (status {d.get('status')})"
        except SystemExit as e: last = f"api error {e}"
        except Exception as e: last = f"{type(e).__name__}: {e}"
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"speech failed: {last}")

def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return round(float(r.stdout.strip()), 2)

FILTER = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.25,areverse,"
          "loudnorm=I=-17:TP=-1.5:LRA=11,apad=pad_dur=0.35")

def to_mp3(wav, mp3):
    mp3.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", FILTER, "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "56k", str(mp3)], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-300:])

def lesson_clip(job):
    lid, i, text = job
    k = key(text)
    mp3 = AUDIO / lid / f"{i + 1:02d}-{k}.mp3"
    if not mp3.exists(): to_mp3(synth(text), mp3)
    return lid, i, {"src": f"audio/{lid}/{mp3.name}", "dur": dur(mp3), "text": text_key(text)}

def drill_track(module, items, title):
    """question -> a pause to answer in your head -> the answer. One MP3 per module."""
    parts = drill_parts(module, items, title)
    k = hashlib.sha256(json.dumps([parts, VOICE, STYLE, MODEL, "v2"]).encode()).hexdigest()[:14]
    mp3 = AUDIO / "drills" / f"module-{module}-{k}.mp3"
    tk = drill_text_key(module, items, title)
    if mp3.exists(): return {"src": f"audio/drills/{mp3.name}", "dur": dur(mp3), "text": tk}
    with cf.ThreadPoolExecutor(4) as ex: wavs = list(ex.map(synth, parts))
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td); lst = []
        def piece(src, name, pad):
            out = td / name
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", FILTER.replace("apad=pad_dur=0.35", f"apad=pad_dur={pad}"), "-ar", "24000", "-ac", "1", str(out)], check=True)
            lst.append(f"file '{out.as_posix()}'")
        piece(wavs[0], "000.wav", 1.2)
        for n in range(len(items)):
            words = len(items[n]["a"].split())
            piece(wavs[1 + 2 * n], f"{n:03d}q.wav", max(5.0, min(9.0, 3.5 + words * 0.11)))     # thinking time scales with the answer
            piece(wavs[2 + 2 * n], f"{n:03d}a.wav", 1.6)
        piece(wavs[-1], "zzz.wav", 0.4)
        (td / "list.txt").write_text("\n".join(lst), encoding="utf-8")
        mp3.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(td / "list.txt"), "-c:a", "libmp3lame", "-b:a", "56k", str(mp3)], check=True)
    return {"src": f"audio/drills/{mp3.name}", "dur": dur(mp3), "text": tk}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*"); ap.add_argument("--sample", action="store_true"); ap.add_argument("--drills", action="store_true")
    ap.add_argument("--workers", type=int, default=5)
    a = ap.parse_args()
    lessons = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "content/lessons").glob("*.json"))]
    if a.sample:
        out = ROOT / "qa/voices"; out.mkdir(parents=True, exist_ok=True)
        text = spoken(next(l for l in lessons if l["id"] == "2-2")["segments"][1]["narration"])
        for v in a.ids or ["Charon", "Sadaltager", "Sulafat", "Iapetus", "Achird"]:
            to_mp3(synth(text, voice=v), out / f"{v}.mp3"); print(f"{v}: {dur(out / (v + '.mp3'))}s  {out / (v + '.mp3')}")
        return
    mpath = ROOT / "data/audio_manifest.json"
    man = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {"lessons": {}, "drills": {}}
    man["voice"], man["model"] = VOICE, MODEL
    if not a.drills:
        jobs = [(l["id"], i, spoken(s["narration"])) for l in lessons if not a.ids or l["id"] in a.ids for i, s in enumerate(l["segments"])]
        res, fails = {}, []
        with cf.ThreadPoolExecutor(a.workers) as ex:
            futs = {ex.submit(lesson_clip, j): j for j in jobs}
            for n, f in enumerate(cf.as_completed(futs), 1):
                j = futs[f]
                try: lid, i, rec = f.result(); res.setdefault(lid, {})[i] = rec
                except Exception as e: fails.append((j[0], j[1] + 1, str(e)[:160]))
                if n % 25 == 0: print(f"  {n}/{len(jobs)} clips", flush=True)
        for l in lessons:
            if l["id"] in res and len(res[l["id"]]) == len(l["segments"]):
                man["lessons"][l["id"]] = [res[l["id"]][i] for i in range(len(l["segments"]))]
                keep = {pathlib.Path(r["src"]).name for r in man["lessons"][l["id"]]}
                for old in (AUDIO / l["id"]).glob("*.mp3"):
                    if old.name not in keep: old.unlink()                # a re-recorded segment replaces its old clip
        for x in fails: print("FAILED", *x)
    if a.drills or not a.ids:
        site = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
        for m in site["modules"]:
            items = [d for l in lessons if str(l["module"]) == str(m["n"]) for d in l["drill"]]
            try:
                man["drills"][str(m["n"])] = drill_track(m["n"], items, m["title"])
                keep = {pathlib.Path(r["src"]).name for r in man["drills"].values()}
                print(f"  drill {m['n']}: {man['drills'][str(m['n'])]['dur']}s, {len(items)} questions", flush=True)
            except Exception as e: print("FAILED drill", m["n"], str(e)[:200])
        for old in (AUDIO / "drills").glob("*.mp3"):
            if old.name not in {pathlib.Path(r["src"]).name for r in man["drills"].values()}: old.unlink()
    mpath.write_text(json.dumps(man, indent=1), encoding="utf-8")
    tot = sum(r["dur"] for v in man["lessons"].values() for r in v)
    print(f"{len(man['lessons'])} lessons with audio, {tot / 60:.0f} minutes; {len(man['drills'])} drill tracks; voice {VOICE} ({MODEL})")

if __name__ == "__main__":
    main()
