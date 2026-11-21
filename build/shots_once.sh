#!/usr/bin/env bash
# Start the local test server only for the length of one screenshot run, then stop it (keeps memory free between runs).
#   bash build/shots_once.sh qa/<scenario>.json [filter]
cd "$(dirname "$0")/.."
export PATH="$PWD/.tools/node:$PATH"
PORT=$((8800 + RANDOM % 700))      # a port of its own, so two runs at once cannot share or kill a server
node build/dev_server.mjs $PORT > qa/dev_once.log 2>&1 &
SRV=$!
for i in $(seq 1 40); do curl -s -o /dev/null "http://localhost:$PORT/login" && break; sleep 0.25; done
GT_BASE="http://localhost:$PORT" node build/shots.mjs "$@"
RC=$?
kill $SRV 2>/dev/null
exit $RC
