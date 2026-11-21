"""What the voice reads, and a fingerprint of it.

Shared by build/tts.py (which records) and build/build_site.py (which publishes), so the two can never disagree
about whether a clip still matches its text. A clip whose fingerprint differs from the lesson's current narration
is stale: the sentence was edited after it was recorded, and the build refuses to ship it.
"""
import hashlib
import json
import re


def spoken(text):
    """What the voice should read: cue markers out, a few things a speech model reads badly spelled the way they sound."""
    t = re.sub(r"\s*\[\[\d+\]\]\s*", " ", text)
    t = t.replace("—", ", ").replace("–", " to ").replace("−", "minus ")
    return re.sub(r"\s+", " ", t).strip()


def text_key(narration):
    """Fingerprint of one segment's spoken text (independent of voice and model)."""
    return hashlib.sha256(spoken(narration).encode("utf-8")).hexdigest()[:16]


def drill_parts(module, items, title):
    """The sentences of a module's drill track, in order: intro, then question and answer for each item, then outro."""
    parts = [f"Recall drill for module {module}: {title}. I ask, you answer in your head, then I answer. Here we go."]
    for n, it in enumerate(items, 1):
        parts += [f"Question {n}. {it['q']}", it["a"]]
    parts.append("That is the drill. Anything you missed, the review cards will bring back.")
    return parts


def drill_text_key(module, items, title):
    return hashlib.sha256(json.dumps(drill_parts(module, items, title), ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
