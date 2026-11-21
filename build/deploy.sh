#!/usr/bin/env bash
# Deploy Ground Truth to Cloudflare Workers. Needs a one-time `wrangler login` (run cf-login.cmd).
#   bash build/deploy.sh            build, create what is missing, deploy, print the URL
# Idempotent: the KV namespace and the two secrets are created only if they do not exist yet.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$PWD/.tools/node:$PATH"
W="npx --yes wrangler"
cd site
$W whoami 2>&1 | grep -qi "not authenticated" && { echo "Not signed in to Cloudflare. Run cf-login.cmd first."; exit 2; }

# 1. the site content must be current and complete
( cd .. && python build/build_site.py )

# 2. KV namespace for progress
if grep -q REPLACED_AT_DEPLOY wrangler.jsonc; then
  id=$($W kv namespace list 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); print(next((n['id'] for n in d if n['title'] in ('PROGRESS','ground-truth-PROGRESS')), ''))" || true)
  if [ -z "$id" ]; then
    id=$($W kv namespace create PROGRESS 2>&1 | python -c "import sys,re; t=sys.stdin.read(); m=re.search(r'\"id\":\s*\"([0-9a-f]{32})\"', t) or re.search(r'id = \"([0-9a-f]{32})\"', t); print(m.group(1) if m else '')")
  fi
  [ -n "$id" ] || { echo "Could not create or find the KV namespace."; exit 3; }
  python - "$id" <<'PY'
import pathlib, sys
p = pathlib.Path("wrangler.jsonc"); p.write_text(p.read_text(encoding="utf-8").replace("REPLACED_AT_DEPLOY", sys.argv[1]), encoding="utf-8")
PY
  echo "KV namespace: $id"
fi

# 3. first deploy creates the Worker; secrets can only be attached to a Worker that exists
$W deploy 2>&1 | tee ../qa/deploy.log | tail -8

# 4. secrets: a session-signing key, and the passphrase you sign in with (kept in .secrets/, never committed)
mkdir -p ../.secrets
have=$($W secret list 2>/dev/null || echo "[]")
if ! echo "$have" | grep -q SESSION_SECRET; then
  python -c "import secrets; print(secrets.token_urlsafe(48), end='')" | $W secret put SESSION_SECRET >/dev/null
  echo "SESSION_SECRET set"
fi
if ! echo "$have" | grep -q '"PASSPHRASE"'; then
  if [ ! -s ../.secrets/passphrase.txt ]; then
    python - <<'PY'
import secrets, pathlib
words = "amber anchor atlas basil beacon birch breeze canyon cedar cobalt comet coral delta ember fable fjord garnet glacier harbor hazel indigo jasper juniper kelp lagoon lantern maple meadow nectar nimbus oasis olive onyx orchid pebble pine quartz quill raven reef saffron sage sierra slate spruce summit tide timber topaz tundra umber valley velvet willow zephyr".split()
pathlib.Path("../.secrets/passphrase.txt").write_text("-".join(secrets.choice(words) for _ in range(5)) + "-" + str(secrets.randbelow(90) + 10), encoding="utf-8")
PY
  fi
  tr -d '\r\n' < ../.secrets/passphrase.txt | $W secret put PASSPHRASE >/dev/null
  echo "PASSPHRASE set (your sign-in passphrase is in .secrets/passphrase.txt)"
fi
url=$(grep -o 'https://[a-z0-9.-]*workers.dev' ../qa/deploy.log | tail -1)
echo "Deployed: $url"
echo "$url" > ../.secrets/url.txt
