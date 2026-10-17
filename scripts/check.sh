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
  printf 'Node.js 24.x is required; found %s.\n' "$node_version" >&2
  exit 1
fi

printf 'Running Python backend and spatial smoke tests...\n'
uv run --locked pytest -q tests sim/test_engine.py
uv run --locked python scripts/health_smoke.py

printf 'Running frontend TypeScript and production build checks...\n'
npm --prefix frontend run typecheck
npm --prefix frontend test
npm --prefix frontend run build

printf 'Checking optional SUMO installation and running its real smoke test when available...\n'
if ! uv run --locked python -m sim.sumo_support --smoke; then
  printf 'Optional SUMO smoke test failed. Basic frontend/backend checks passed; SUMO is not marked ready.\n' >&2
fi
printf 'Project checks completed.\n'
