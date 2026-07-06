#!/usr/bin/env bash
# Start (or restart) the progress follow-along server. ONE command, idempotent, prints the URL.
# Safe to run repeatedly and from workflow start (rider 8): kills any stale server on the port,
# then serves progress/ detached so it survives this shell. Never blocks.
#   usage: progress/serve.sh [port]   (default 8787)
set -euo pipefail
PORT="${1:-8787}"
HERE="$(cd "$(dirname "$0")" && pwd)"

# If something already answers on the port, assume it's us and just report (non-event).
if curl -sf -o /dev/null "http://localhost:${PORT}/feed.json" 2>/dev/null; then
  echo "progress server already up → http://localhost:${PORT}"
  exit 0
fi
# else (re)launch: clear any stale pid, start detached
pid=$(lsof -ti tcp:"$PORT" 2>/dev/null || true)
[ -n "$pid" ] && kill "$pid" 2>/dev/null || true
sleep 0.3
nohup python3 -m http.server "$PORT" --directory "$HERE" >"$HERE/server.log" 2>&1 &
echo $! >"$HERE/.server.pid"
sleep 0.6
if curl -sf -o /dev/null "http://localhost:${PORT}/index.html"; then
  echo "progress server → http://localhost:${PORT}  (pid $(cat "$HERE/.server.pid"))"
else
  echo "WARN: progress server did not answer on ${PORT}; see ${HERE}/server.log" >&2
  exit 1
fi
