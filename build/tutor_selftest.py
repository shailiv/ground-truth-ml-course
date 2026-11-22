"""Read the tutor's streamed reply to the post-deploy self-test question (on stdin) and say in one line how it went.
Used by build/smoke.sh. Never fails the deploy: the site is fine without a tutor; this only reports."""
import json
import sys

text, error, done = "", "", False
raw = sys.stdin.read()
for line in raw.splitlines():
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    if ev.get("t") == "delta":
        text += ev.get("text", "")
    elif ev.get("t") == "error":
        error = ev.get("message", "an error with no message")
    elif ev.get("t") == "done":
        done = True
    elif ev.get("message") and not error:          # a refusal sent as plain JSON, such as the daily ceiling
        error = ev["message"]
if text.strip() and done:
    print("  Tutor self-test: Claude answered through the site's API key (%r)." % text.strip()[:40])
elif error:
    print("  TUTOR SELF-TEST FAILED: " + error)
    print("  The site itself is fine. Until this is fixed, questions fall back to the relay or to opening Claude.")
else:
    print("  TUTOR SELF-TEST: no answer came back (%d bytes received). The site itself is fine." % len(raw))
