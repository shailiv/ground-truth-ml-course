"""Ask the live tutor one fixed question and say in one line how it went.

    python build/tutor_health.py            uses .secrets/relay.json (the site's address and its machine secret)

It calls the site's self-test door (/api/relay/selftest), which is opened by the relay secret, not by the owner's
passphrase: so it can be run by tooling without signing in as the owner. The secret is read from the file and sent
in a header; it is never printed and never appears on a command line. The question carries no learner content and
costs about a cent of the plan's included API credit.

Exit status: 0 the tutor answered (or there is no API key and nothing to test), 1 it did not.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

cfg_path = pathlib.Path(__file__).resolve().parent.parent / ".secrets" / "relay.json"
if not cfg_path.exists():
    print("  Tutor check: the site has not been deployed from this computer (.secrets/relay.json is missing).")
    sys.exit(1)
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
req = urllib.request.Request(cfg["url"].rstrip("/") + "/api/relay/selftest", method="POST", data=b"{}",
                             headers={"authorization": "Bearer " + cfg["secret"], "content-type": "application/json", "user-agent": "ground-truth-health"})
try:
    with urllib.request.urlopen(req, timeout=150) as res:
        raw = res.read().decode("utf-8", "replace")
except urllib.error.HTTPError as e:
    print("  TUTOR CHECK FAILED: the site answered HTTP %s to its own self-test (404 means the live site is older than this code; 403 means the relay secret differs)." % e.code)
    sys.exit(1)
except Exception as e:  # noqa: BLE001 - a network failure of any kind is reported the same way
    print("  TUTOR CHECK FAILED: could not reach the site (%s)." % type(e).__name__)
    sys.exit(1)

text, error, done, plain = "", "", False, None
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
        done = ev
    elif "api" in ev or "message" in ev:
        plain = ev
if text.strip() and done:
    tok = done.get("tokens") or {}
    print("  Tutor check: Claude answered through the site's API key: %r (model %s, %s tokens in, %s out)."
          % (text.strip()[:40], done.get("model"), tok.get("in"), tok.get("out")))
    sys.exit(0)
if plain is not None and plain.get("api") is False:
    print("  Tutor check: the site has no Claude API key, so there is nothing to test (the relay or the link is used).")
    sys.exit(0)
print("  TUTOR CHECK FAILED: " + (error or (plain or {}).get("message") or "no answer came back (%d bytes)" % len(raw)))
print("  The site itself is fine. Until this is fixed, a question shows this message and offers to open Claude instead.")
sys.exit(1)
