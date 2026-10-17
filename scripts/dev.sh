#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

for command_name in uv npm node; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf '%s was not found. Install prerequisites and run scripts/setup.sh first.\n' "$command_name" >&2
    exit 1
  fi
done
node_version="$(node --version)"
node_major="${node_version#v}"
node_major="${node_major%%.*}"
if [[ "$node_major" != "24" ]]; then
  printf 'Node.js 24.x is required; found %s. Run scripts/setup.sh after selecting Node.js 24.\n' "$node_version" >&2
  exit 1
fi
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  printf 'Frontend dependencies are missing. Run scripts/setup.sh first.\n' >&2
  exit 1
fi

(cd "$ROOT" && exec uv run --locked uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!
(cd "$ROOT/frontend" && exec npm exec --workspace @arteria/web -- next dev --hostname 127.0.0.1 --port 3000) &
FRONTEND_PID=$!

cleanup() {
  trap - EXIT INT TERM
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" 2>/dev/null || true
  wait "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

printf 'ARTERIA development services are starting:\n'
printf '  Frontend: http://127.0.0.1:3000\n'
printf '  Backend:  http://127.0.0.1:8000/health\n'
printf 'Press Ctrl+C to stop both services.\n'

while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  wait "$BACKEND_PID" || status=$?
  printf 'Backend process stopped unexpectedly (exit %s).\n' "${status:-0}" >&2
  exit "${status:-1}"
fi
wait "$FRONTEND_PID" || status=$?
printf 'Frontend process stopped unexpectedly (exit %s).\n' "${status:-0}" >&2
exit "${status:-1}"
