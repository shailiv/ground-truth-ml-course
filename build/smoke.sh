#!/usr/bin/env bash
# Is this copy of the site really locked, and does it work once signed in?
#   bash build/smoke.sh <base-url> <file-holding-the-passphrase>
# Used by build/deploy.sh against the live site, and against `wrangler dev` before anything is deployed.
# Exits 0 only if every check passes.
set -uo pipefail
cd "$(dirname "$0")/.."
url="${1%/}"; pass="$2"; bad=0
code() { curl -s -o /dev/null -w '%{http_code}' --max-time 30 --path-as-is "$@"; }
want() { [ "$2" = "$3" ] || { echo "  FAIL  $1: answered $2, wanted $3"; bad=1; }; }
clip=$(python -c "import json; d=json.load(open('site/public/data/course.json', encoding='utf-8')); print(d['lessons'][0]['audio'][0]['src'])")

# signed out: nothing of the course is readable, by any spelling of a path
for p in / /index.html /data/course.json /data/assistant-pack.md /js/app.js /js/merge.js /reports/plain.html "/$clip"; do
  want "signed out, $p" "$(code "$url$p")" 303
done
for p in '/fonts/..%2fdata/course.json' '/css/..%5cdata/course.json' '/fonts/%2e%2e/data/course.json' '/fonts/../data/course.json' '//data/course.json'; do
  c=$(code "$url$p"); case "$c" in 400|404|303) ;; *) echo "  FAIL  $p answered $c without a sign-in"; bad=1;; esac
done
want "signed out, the progress API" "$(code "$url/api/progress")" 401
want "signed out, the tutor" "$(code "$url/api/tutor/status")" 401
want "the relay door without its secret" "$(code "$url/api/relay/next")" 403
# the sign-in page and only what it needs
for p in /login /css/app.css /css/fonts.css /js/login.js /favicon.svg; do want "the sign-in page loads $p" "$(code "$url$p")" 200; done
want "a wrong passphrase" "$(code -d 'passphrase=definitely-not-it' "$url/login")" 303

# signed in
jar=$(mktemp)
want "signing in" "$(code -c "$jar" --data-urlencode "passphrase@$pass" "$url/login")" 303
want "signed in, the course" "$(code -b "$jar" "$url/")" 200
curl -s --max-time 30 -b "$jar" "$url/" | grep -q 'id="app"\|<main' || { echo "  FAIL  signed in, / is not the course page"; bad=1; }
curl -s -D - -o /dev/null --max-time 30 -b "$jar" "$url/" | grep -qi '^content-security-policy:' || { echo "  FAIL  the security headers are missing"; bad=1; }
want "signed in, the lessons" "$(code -b "$jar" "$url/data/course.json")" 200
want "signed in, a whole audio clip" "$(code -b "$jar" "$url/$clip")" 200
want "signed in, a byte range of audio (Safari needs 206)" "$(code -b "$jar" -H 'Range: bytes=0-99' "$url/$clip")" 206
want "signed in, reading progress" "$(code -b "$jar" "$url/api/progress")" 200
want "signed in, the tutor status" "$(code -b "$jar" "$url/api/tutor/status")" 200
want "signing out by link does nothing" "$(code -b "$jar" "$url/logout")" 303
want "still signed in after that" "$(code -b "$jar" "$url/")" 200
# the tutor, when the site has its own Claude API key: one real question, so a wrong key shows up now and not in a lesson
if [ "${TUTOR_SELFTEST:-}" = "1" ]; then
  curl -s --max-time 120 -b "$jar" -H 'content-type: application/json' -d '{"question":"Reply with the single word: ready","lesson":"","moment":"(a self-test run right after a deploy)","history":[]}' "$url/api/tutor/ask" | python build/tutor_selftest.py
fi
rm -f "$jar"

if [ "$bad" = "1" ]; then echo "SMOKE TEST FAILED for $url"; exit 1; fi
echo "Smoke test passed: locked when signed out, working when signed in."
