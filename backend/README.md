# ARTERIA backend

FastAPI API v0.3: analyze → propose → evaluate, with SQLite persistence, validated
interventions, synthetic provenance and frontend-compatible response shapes.
No cloud API key or SUMO installation is needed for the demo.

## macOS startup

From the repository root:

```sh
uv sync --locked
uv run --locked uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs. The authoritative app is `backend.main:app`.
The legacy `python -m backend.server` command now launches the same FastAPI app,
instead of a separate server with conflicting behavior.

```sh
uv run --locked pytest -q
uv run --locked python scripts/health_smoke.py
uv run --locked python -m backend.demo_client
```

The final command runs a complete flow against the running API and prints all
request/response pairs. Use `--base-url http://127.0.0.1:8011` for another port.

CORS defaults include localhost and 127.0.0.1 on ports **3000** and **5173**.
An existing `ARTERIA_CORS_ORIGINS` environment/.env value overrides those defaults;
include port 3000 if using Next.js.

SQLite lives in ignored `backend/.data/arteria.sqlite3`. Override with
`ARTERIA_DB_PATH=/absolute/path/arteria.sqlite3`. IDs and results survive reloads
and worker restarts. Transactions preserve the first result for repeated requests;
records are immutable and each record category is capped at 1000. At capacity,
archive the database or explicitly configure a fresh path. No public destructive
reset endpoint is exposed. Local SQLite is not distributed/cloud persistence;
there is no authentication or per-user isolation, so run locally for this demo.

## Scope and integration

See [current frontend contract](../docs/DEMO_API.md),
[captured flow](../docs/demo-flow.json), and [handoff](FRONTEND_HANDOFF.md).
Supported demo contexts: `iasi-demo-intersection`, `podu-ros`, `copou`, `centru`,
`tatarasi`, `alexandru`, plus their `preview-` aliases. These are UI bookmarks,
not certified neighborhood boundaries or real traffic studies. All use the same
synthetic two-phase intersection assumptions unless explicit inputs are supplied.

Optional polygons on the synthetic signal-timing endpoints are checked for valid
geometry, coordinate bounds, a 1 m²–5 km² area limit and containment of the
selected bookmark. This does not verify that a polygon is an official neighborhood
boundary. Historical `data_as_of` requests are rejected.

Signal timing is the sole intervention. Both phases require at least 10 seconds
green, with a fixed cycle and 10 seconds lost time. Default recommendations move
25%, 50%, or 100% toward demand-proportional allocation. Already balanced inputs
may produce no-ops. `parameters.ns_green_seconds` on `/propose` requests an exact
user-selected timing, validated against that baseline; copy the returned
intervention into `/evaluate`. Timing changes require no land take, so any valid
positive `max_affected_area` constraint is satisfied in this synthetic catalog.
These are demo feasibility checks, not a real-world safety approval.

Delay formula: `red² / (2 * cycle) + 60 * max(0, demand / capacity - 1)` seconds/vehicle;
`capacity = 1800 * green / cycle` vehicles/hour. Mean delay is demand-weighted.
Engine/source version is `demo-2`; calculations are uncalibrated synthetic estimates.
Evaluations preserve baseline demand, cycle, lost time and original evidence.
Positive and negative deltas are returned; improvement is not guaranteed.

## Simulation boundary

`backend/simulation_adapter.py` owns deterministic synthetic signal-timing
evaluation. The separate [SIM v3 spatial API](SPATIAL_API.md) loads the in-tree
`sim/` package and performs pedestrian graph analysis and stored graph comparisons.
It supports a clearly labeled fixture or the server-validated OSM neighborhood
catalog. OSM feature layers that were not queried stay unknown. Graph candidates
do not establish physical feasibility, and this API does not run SUMO or traffic
simulation. Explicit SUMO live/offline/replay requests on the signal-timing API
return `503 sumo_unavailable` without fallback, even if SUMO is installed.

The spatial study API now stores SIM urban issues, its evidence-linked solution
plan, problem GeoJSON, and the immutable AI packet. Optional OpenAI Responses API
planning is available through [AI_PLANNING_API.md](AI_PLANNING_API.md), disabled
by default, and requires server-side credentials. It does not add traffic
telemetry, calibrated simulation, certified boundaries, construction feasibility,
authentication, SUMO jobs/SSE, or cloud storage. `API_ENDPOINTS.md` remains an
aspirational legacy reference; its numeric traffic figures are not observations.
