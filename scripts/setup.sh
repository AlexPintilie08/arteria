#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

case "$(uname -s)" in
  Darwin) platform="macOS $(uname -m)" ;;
  Linux) platform="Linux $(uname -m)" ;;
  *) printf 'Unsupported setup platform: %s\n' "$(uname -s)" >&2; exit 1 ;;
esac
printf 'ARTERIA setup on %s\n' "$platform"

if ! command -v node >/dev/null 2>&1; then
  printf 'Node.js was not found. Install Node.js 24 LTS from https://nodejs.org/en/download/ and reopen your terminal.\n' >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  printf 'npm was not found. Install Node.js 24 LTS from https://nodejs.org/en/download/; npm is included with Node.js.\n' >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  printf 'uv was not found. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh. Or use https://docs.astral.sh/uv/getting-started/installation/, then reopen your terminal.\n' >&2
  exit 1
fi

node_version="$(node --version)"
node_major="${node_version#v}"
node_major="${node_major%%.*}"
if [[ "$node_major" != "24" ]]; then
  printf 'Node.js 24.x is required; found %s. Install Node.js 24 LTS from https://nodejs.org/en/download/.\n' "$node_version" >&2
  exit 1
fi
printf 'Node.js %s; npm %s\n' "$node_version" "$(npm --version)"
uv --version

export UV_PYTHON_INSTALL_DIR="$ROOT/.uv-python"
if uv python find --managed-python 3.12 >/dev/null 2>&1; then
  printf 'Using uv-managed Python 3.12 at %s\n' "$(uv python find --managed-python 3.12)"
else
  printf 'Acquiring a project-local Python 3.12 runtime with uv in %s...\n' "$UV_PYTHON_INSTALL_DIR"
  uv python install 3.12 --install-dir "$UV_PYTHON_INSTALL_DIR" --no-bin
  uv python find --managed-python 3.12 >/dev/null
fi
printf 'Installing the locked Python environment...\n'
uv sync --locked
printf 'Installing locked frontend dependencies...\n'
npm --prefix frontend ci

printf 'Checking optional SUMO availability and Python integration...\n'
if ! uv run --locked python -m sim.sumo_support --smoke; then
  printf 'SUMO was detected but its optional smoke test did not pass. Basic frontend/backend startup remains available.\n' >&2
fi

printf 'Running project validation...\n'
bash "$ROOT/scripts/check.sh"
printf 'ARTERIA setup completed.\n'
