#!/usr/bin/env bash
# Deploy Ground Truth to Cloudflare Workers. Needs a one-time `wrangler login` (go-live.cmd does both).
#   bash build/deploy.sh            test, build, create what is missing, deploy, check the live site is locked
# Safe to run again: the KV namespace, the secrets and the passphrase are created once and then reused.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$PWD/.tools/node:$PATH"
W="npx --yes wrangler"
mkdir -p .secrets

who=$(cd site && $W whoami 2>&1 || true)
if grep -qi "not authenticated" <<<"$who"; then echo "Not signed in to Cloudflare. Run go-live.cmd (or: cd site && npx wrangler login)."; exit 2; fi

# 1. nothing goes out unless the lock and the progress merge pass their tests, and every lesson has its audio
node build/test_site.mjs
python build/build_site.py --prune

cd site
# 2. KV namespace for progress. Its id goes into wrangler.deploy.jsonc, which is not committed.
id=""
[ -f wrangler.deploy.jsonc ] && id=$(grep -o '"id": *"[0-9a-f]\{32\}"' wrangler.deploy.jsonc | grep -o '[0-9a-f]\{32\}' | head -1 || true)
if [ -z "$id" ]; then
  id=$($W kv namespace list 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); print(next((n['id'] for n in d if n['title'] in ('PROGRESS','ground-truth-PROGRESS')), ''))" 2>/dev/null || true)
fi
if [ -z "$id" ]; then
  id=$($W kv namespace create PROGRESS 2>&1 | python -c "import sys,re; t=sys.stdin.read(); m=re.search(r'\"id\":\s*\"([0-9a-f]{32})\"', t) or re.search(r'id = \"([0-9a-f]{32})\"', t); print(m.group(1) if m else '')" || true)
fi
[ -n "$id" ] || { echo "Could not create or find the KV namespace for progress."; exit 3; }
python - "$id" <<'PY'
import pathlib, sys
src = pathlib.Path("wrangler.jsonc").read_text(encoding="utf-8")
assert "REPLACED_AT_DEPLOY" in src, "wrangler.jsonc must keep the placeholder"
pathlib.Path("wrangler.deploy.jsonc").write_text(src.replace("REPLACED_AT_DEPLOY", sys.argv[1]), encoding="utf-8")
PY

# 3. secrets, generated once and kept in .secrets/ (never committed): the session-signing key, the passphrase you
#    sign in with, and the secret the tutor relay uses. They are uploaded together with the code, so the site is
#    never live without them.
python - <<'PY'
import json, pathlib, secrets
f = pathlib.Path("../.secrets/worker-secrets.json")
s = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
words = "amber anchor atlas basil beacon birch breeze canyon cedar cobalt comet coral delta ember fable fjord garnet glacier harbor hazel indigo jasper juniper kelp lagoon lantern maple meadow nectar nimbus oasis olive onyx orchid pebble pine quartz quill raven reef saffron sage sierra slate spruce summit tide timber topaz tundra umber valley velvet willow zephyr".split()
plain = "abcdefghjkmnpqrstuvwxyz23456789"                     # no look-alikes (0/o, 1/l/i)
old = pathlib.Path("../.secrets/passphrase.txt")
if "PASSPHRASE" not in s:                                      # four words and eight random characters: about 63 bits
    s["PASSPHRASE"] = old.read_text(encoding="utf-8").strip() if old.exists() and old.read_text(encoding="utf-8").strip() else \
        "-".join(secrets.choice(words) for _ in range(4)) + "-" + "".join(secrets.choice(plain) for _ in range(4)) + "-" + "".join(secrets.choice(plain) for _ in range(4))
s.setdefault("SESSION_SECRET", secrets.token_urlsafe(48))
s.setdefault("RELAY_SECRET", secrets.token_urlsafe(40))
f.write_text(json.dumps(s), encoding="utf-8")
old.write_text(s["PASSPHRASE"], encoding="utf-8")
PY

# 4. deploy. Wrangler stays attached to the window (on a brand-new account it asks for a workers.dev name), and
#    the address is read from the record Wrangler writes, not scraped from what it prints.
rm -f ../.secrets/deploy.ndjson
WRANGLER_OUTPUT_FILE_PATH=../.secrets/deploy.ndjson $W deploy -c wrangler.deploy.jsonc --secrets-file ../.secrets/worker-secrets.json
url=$(python ../build/deploy_url.py)
[ -n "$url" ] || { echo "Deployed, but the workers.dev address could not be read. Find it in the Cloudflare dashboard under Workers, put it in .secrets/url.txt, and run this again."; exit 4; }
echo "$url" > ../.secrets/url.txt
python - "$url" <<'PY'
import json, pathlib, sys
s = json.loads(pathlib.Path("../.secrets/worker-secrets.json").read_text(encoding="utf-8"))
pathlib.Path("../.secrets/relay.json").write_text(json.dumps({"url": sys.argv[1], "secret": s["RELAY_SECRET"], "model": "sonnet"}), encoding="utf-8")
PY

# 5. is the live site really locked, and does it work once signed in? Fail loudly if not.
echo "Checking the live site..."
sleep 4
cd ..
if ! bash build/smoke.sh "$url" .secrets/passphrase.txt; then
  echo; echo "The site is deployed at $url but FAILED the checks above. Do not rely on it until they pass."; exit 5
fi

echo
echo "Live and locked: $url"
echo "Passphrase:      in .secrets/passphrase.txt (show-login.cmd prints it)"
echo "Tutor relay:     tutor-relay.cmd starts it on this computer; without it, questions open in Claude instead"
