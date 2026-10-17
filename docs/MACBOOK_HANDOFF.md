# MacBook handoff

## Published source

Use the **`main`** branch. It contains the integrated frontend, FastAPI backend,
SIM v3, and the local OSM neighborhood explorer. Integration PR
[#2](https://github.com/AlexPintilie08/arteria/pull/2) merged the full-stack
source at `36076f71c9d41e07b91fd7c1c4e51e70cac86b6d`; GitHub Actions passed on
Windows x64, macOS ARM64, and macOS Intel for that revision in
[the post-merge run](https://github.com/AlexPintilie08/arteria/actions/runs/39071420328).
Clone or update `main` to get the latest handoff documentation and project changes.

## Prerequisites

- macOS and Git.
- Node.js **24.x** and its bundled npm. The repository pins 24 in `.nvmrc`; install
  the macOS ARM64 or x64 package from the [official Node.js 24 downloads](https://nodejs.org/en/download/archive/v24/).
- `uv`. If it is not installed, use Astral's installer and open a new terminal:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

  See the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

CI has verified this project on macOS 15 Apple Silicon and Intel runners. The
project selects Python 3.12 in `.python-version` and restricts Python versions in
`pyproject.toml`; `uv.lock` pins the package environment and `uv` can manage the
Python interpreter for you.

## Clone and install

```bash
git clone https://github.com/AlexPintilie08/arteria.git
cd arteria
git switch main
node --version  # must report v24.x
uv --version
```

The repository setup script prepares Python 3.12, installs the locked Python and
frontend dependencies, runs the checks, and tests SUMO only if it is available:

```bash
bash scripts/setup.sh
```

To install each environment manually from the repository root:

```bash
export UV_PYTHON_INSTALL_DIR="$PWD/.uv-python"
if ! uv python find --managed-python 3.12 >/dev/null 2>&1; then
  uv python install 3.12 --install-dir "$UV_PYTHON_INSTALL_DIR" --no-bin
fi
uv sync --locked
cd frontend
npm ci
cd ..
```

The setup creates local ignored environments and dependencies. No AI key or SUMO
installation is needed to start the web MVP.

## Start the application

Open two terminals in the repository root.

Terminal 1, start FastAPI:

```bash
uv run --locked uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, start Next.js:

```bash
cd frontend
npm run dev
```

Or start both services together with `bash scripts/dev.sh` and stop them with
Ctrl+C. Default settings connect the frontend to `http://localhost:8000` and
allow CORS from port 3000. No `.env.local` file is required. To configure an
optional MapLibre basemap, set `NEXT_PUBLIC_MAP_STYLE_URL` in the ignored file
`frontend/web/.env.local`; a blank style uses a neutral canvas while the bundled
catalog and its geometry remain available.

| Service | URL |
| --- | --- |
| Presentation homepage | <http://localhost:3000/> |
| Product workspace | <http://localhost:3000/app> |
| Backend health | <http://127.0.0.1:8000/health> |
| FastAPI OpenAPI | <http://127.0.0.1:8000/docs> |

## Run checks

From the repository root, the complete project check is:

```bash
bash scripts/check.sh
```

It runs the backend and SIM suites, health smoke test, frontend typechecks and
tests, production build, and a non-blocking SUMO smoke check when the executable
is available. To run the Python tests directly, include the SIM suite explicitly:

```bash
uv run --locked pytest -q tests sim/test_engine.py
```

Frontend checks can also be run from `frontend/`:

```bash
npm run typecheck
npm test
npm run build
```

## What needs network access or local software

- The Iași catalog is bundled in Git: 24 OSM Polygon/MultiPolygon records and 7
  point-only records. It preserves source attribution and ODbL licensing. The
  OSM place extents are not official administrative boundaries.
- A fresh clone has **no OSM graph cache**. Browsing the catalog works offline;
  an OSM graph study needs internet access to query OpenStreetMap/Overpass. The
  backend cache lives under ignored `backend/.data/osm-cache/`, is not published,
  and is not required for online analysis. Uncached acquisition may take up to
  the API's 90-second limit.
- The graph API analyzes pedestrian networks and evaluates stored graph
  comparisons. It does not simulate vehicle traffic. The signal-timing demo uses
  explicitly synthetic inputs. Cloud AI generation is not connected.
- SUMO and `netconvert` are optional for basic startup. If their executables are
  missing, SUMO evaluation reports unavailable; the web and backend services
  still run. The project check reports SUMO separately from core checks.
- SQLite databases, OSM cache files, `.env.local`, `.venv`, `.uv-python`,
  `node_modules`, and build outputs are local and ignored. They are created as
  needed and are not part of the source handoff. No credentials are required for
  the documented workflows.
- Running the optional Android app also requires the Android SDK and an emulator
  or device; these are not needed for the web MVP.

## Git workflow

Fetch teammate updates and bring `main` forward before starting new work:

```bash
git fetch origin --prune
git switch main
git pull --ff-only origin main
```

Create a feature branch, commit, and push it:

```bash
git switch -c feat/short-description
git add <files>
git commit -m "Describe the change"
git push -u origin feat/short-description
```

Open a pull request from that branch to `main` in GitHub. Keep changes on your
feature branch until the PR checks pass and it is merged.
