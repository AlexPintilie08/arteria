# Optional pedestrian graph API

This API runs the actual `sim` library independently from the synthetic
signal-timing endpoints. It does not simulate vehicle traffic. The existing
`/analyze`, `/propose`, `/evaluate` wire contract remains unchanged.

## Enable without modifying sim/ or merging another branch

From the repository root, after fetching the colleague's branch when needed:

```sh
python3 -m uv run --locked python -m backend.prepare_sim
python3 -m uv run --locked uvicorn backend.main:app --reload --port 8000
```

`prepare_sim` exports the **locally available** `origin/feat/sim-engine` commit
into ignored `backend/.data/sim-engine/<commit>/`. It does not fetch, commit,
switch branches, merge, or alter the tracked `sim/` tree. It preserves the source
and license files and records the exact commit in an active manifest. The verified
revision is `752c92da9184effc9b87704e0868320f569454ea`.

Alternatively set `ARTERIA_SIM_ROOT` to an existing checkout root containing `sim/`,
and `ARTERIA_SIM_REVISION` to its commit/version. Unversioned external checkouts are
explicitly reported as `external-unversioned`. This is local trusted Python code,
not a package path accepted from HTTP requests. When sim is integrated into the
main checkout later, the environment variable can point to that checkout.

## Complete graph flow

1. `POST /api/v1/spatial/studies`

```json
{"source":"fixture","sample_count":16,"max_candidates":3,"seed":"arteria-spatial-v1"}
```

Returns 201 with `study_id`, `baseline_id`, `created_at`, `source`, `engine_revision`,
`calculation:"pedestrian_graph"`, native `analysis`, native `alternatives`, and
warnings. `source:"fixture"` uses the sim library's tiny synthetic graph, with no
OSM download. It cannot be combined with an area, preventing synthetic results
from being attributed to a selected real neighborhood.

`analysis` preserves indicators, issues, layers, GeoJSON, network metrics and
provenance from sim. `alternatives.ranked_candidates` preserves intervention
geometry, screening, shared-sample ranking, impacts and separate diagnostic routes.
The nested native payload is the sim engine's versioned schema, **not** the frontend's
signal-timing response schema. No population or observed journeys are inferred.

2. `GET /api/v1/spatial/studies/{study_id}/candidates`

Returns the saved baseline ID and ranked candidate objects. An empty array is a
valid outcome when no candidate passes screening. Do not manufacture alternatives.

3. `POST /api/v1/spatial/studies/{study_id}/evaluate`

```json
{
  "baseline_id":"<baseline_id from study>",
  "candidate_id":"<candidate_id from candidates>",
  "intervention":{"copy":"replace this object with the complete returned intervention"}
}
```

Returns `execution:"stored_graph_comparison"`, `sumo_executed:false`, `source`,
`evaluated_at`, the exact intervention and its native `impact` (per-route Before/After,
signed deltas, reachability transitions, aggregate results, units and assumptions).
All candidate comparisons are computed together when the study is created, on the
same original snapshot and common route sample. Selection reads that saved result;
it does **not** claim a fresh simulation or recalculate against changed inputs.
Candidate-specific diagnostic routes remain separate from shared-sample ranking.

`GET /api/v1/spatial/studies/{study_id}` retrieves the complete immutable study.
Studies persist in the same SQLite database as the main demo. Graph objects are
not persisted, so arbitrary edits/re-evaluation require a new study; this API accepts
only exact stored candidates.

## Actual OSM acquisition (optional, network required)

Use `source:"osm"` with an explicit `area` containing a valid Polygon, city_id,
area_id, boundary_source and EPSG:4326. Bounds are restricted to the Iași study
envelope, at most 5 km² and 5 km extent. Only the walking graph is requested.
A user polygon is not a certified neighborhood boundary. The engine's original
OSM provenance, coverage warnings and ODbL attribution remain in the response.
Backend cache files live under `backend/.data/osm-cache/`, not sim/.

No live OSM download was used in the backend verification. An OSM request never
falls back to fixture data. Missing layers remain unknown according to sim.

## Operational limits and errors

One engine subprocess per API worker, a 90-second execution deadline, 1–64 sampled
pairs, at most 3 returned and 6 evaluated candidates, pool limit 30 and route
geometry limit 16. Use a client timeout above 90 seconds for OSM acquisition; the
current shared frontend client's default 30 seconds is shorter. This is a synchronous
bounded API, not a background job/SSE system. A client disconnect does not itself
cancel the child; the server deadline still applies. Use a single API worker for a
single total concurrent graph calculation.

422 invalid request/geometry; 404 unknown study/candidate; 409 baseline or intervention
mismatch; 503 missing/busy engine; 504 terminated deadline; 502 failed/incompatible
engine result. Every error uses the standard error envelope. No synthetic fallback.
The subprocess has the project's Python environment; no new dependency is added.

```sh
python3 -m uv run --locked pytest -q
python3 -m uv run --locked python -m backend.spatial_demo_client
```

The optional real-engine integration test runs when a snapshot is configured;
otherwise it is explicitly skipped. Unit/API failure tests always run.
