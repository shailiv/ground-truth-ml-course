"""Store the Claude API key the tutor uses. Run by add-tutor-key.cmd.

The key is pasted at a hidden prompt, kept in .secrets/worker-secrets.json (which git ignores) and uploaded to
Cloudflare as a Worker secret with the next deploy. It is never printed, apart from its last four characters.

    python build/set_tutor_key.py            store or replace the key
    python build/set_tutor_key.py --remove   take it out again (the tutor falls back to the relay or the link)
"""
import getpass
import json
import pathlib
import sys

f = pathlib.Path(__file__).resolve().parent.parent / ".secrets" / "worker-secrets.json"
s = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

if "--remove" in sys.argv:
    if s.pop("ANTHROPIC_API_KEY", None) is None:
        print("  There was no key stored.")
    else:
        f.write_text(json.dumps(s), encoding="utf-8")
        print("  Key removed from this computer. Run go-live.cmd to remove it from the site too.")
    sys.exit(0)

print("  Paste the API key and press Enter. Nothing will appear as you paste: that is on purpose.")
key = getpass.getpass("  Key: ").strip().strip('"').strip("'")
if not key:
    print("  No key entered; nothing changed.")
    sys.exit(1)
if not key.startswith("sk-ant-") or len(key) < 40 or any(c.isspace() for c in key):
    print("  That does not look like a Claude API key (they start with sk-ant- and are about 100 characters). Nothing changed.")
    sys.exit(1)
s["ANTHROPIC_API_KEY"] = key
f.parent.mkdir(exist_ok=True)
f.write_text(json.dumps(s), encoding="utf-8")
print(f"  Key stored on this computer (it ends in ...{key[-4:]}).")
