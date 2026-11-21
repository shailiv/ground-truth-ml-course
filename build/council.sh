#!/usr/bin/env bash
# Usage: build/council.sh <tag> <file-to-review> <prompt-file> <model> [more -f files...]
# Sends one council seat's prompt + the document to a Gemini model and saves the review.
set -u
cd "$(dirname "$0")/.."
tag="$1"; doc="$2"; prompt="$3"; model="$4"; shift 4
extra=()
for f in "$@"; do extra+=(-f "$f"); done
python "$HOME/.claude/skills/gemini/scripts/gemini.py" ask -m "$model" --thinking high -f "$doc" "${extra[@]}" "@$prompt" \
  -o "docs/council/$tag.md" > /dev/null 2> "docs/council/$tag.log"
echo "$tag: exit $? $(tail -1 "docs/council/$tag.log" | cut -c1-160)"
