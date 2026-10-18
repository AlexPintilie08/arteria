# SIM pedestrian graph and AI planning API

The spatial API runs the repository's in-tree SIM library in a bounded worker
process. It provides pedestrian-network analysis and graph comparisons. It does
not run SUMO or traffic-signal simulation. The existing `/analyze`, `/propose`,
and `/evaluate` endpoints remain the separate synthetic signal-timing API.

## Start the integrated application

From the repository root:

```powershell
uv sync --locked
uv run --locked uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

By default, `backend.spatial_adapter` loads `sim/` from this checkout and reports
the current repository revision. Set `ARTERIA_SIM_ROOT` to use a different trusted
checkout; `ARTERIA_SIM_REVISION` can identify that checkout. The HTTP API never
accepts a Python path. OSM cache files are stored under ignored
`backend/.data/osm-cache/`.

The frontend preview catalog is generated from `sim/iasi-neighborhoods.geojson`.
Refresh it after updating the SIM catalog with
`uv run --locked python frontend/scripts/export_sim_geography.py`. The exporter
does not fetch OSM. Attribution and licensing notes are in
`sim/NEIGHBORHOODS_LICENSE.md`.

## Create a study

`POST /api/v1/spatial/studies` accepts either the offline synthetic fixture:

```json
{"source":"fixture","sample_count":16,"max_candidates":3,"seed":"arteria-spatial-v1"}
```

or a canonical ID from the in-repository OSM neighborhood catalog:

```json
{"source":"osm","neighborhood_id":"osm-w-670153116","sample_count":16,"max_candidates":3,"seed":"arteria-spatial-v1"}
```

OSM geometry is looked up and validated server-side. Clients cannot provide an
arbitrary polygon. Point-only catalog entries remain points and are rejected as
study areas. Polygon areas beyond SIM's standard 5 km² or 5 km extent limits are
reported as requiring controlled analysis. OSM place extents are mapped place
boundaries, not official administrative boundaries.

The worker requests the walking graph and bounded feature categories for schools,
healthcare, public transport, and crossings. Unqueried layers remain `unknown`,
and their accessibility indicators remain unknown. Live OSM requests need network
access and preserve SIM's source provenance, coverage warnings, and OpenStreetMap
attribution. An OSM failure never falls back to the synthetic fixture.

The 201 response includes `study_id`, `baseline_id`, `created_at`, `source`,
`engine_revision`, `analysis`, native `alternatives`, `proposal_options`,
`proposal_validation`, and `evidence_packet`. It also returns `urban_issues`,
`solution_plan`, `ai_evidence_packet`, `problem_locations_geojson`, and the
SIM-generated `evidence_packet_sha256`. Native payloads retain SIM geometry,
source provenance, uncertainty, and warnings. Proposal validation reports graph
evidence and evaluation status; it does not certify physical feasibility or
safety. Results do not imply population impacts or observed journeys.

## Retrieve and compare candidates

`GET /api/v1/spatial/studies/{study_id}` returns the saved immutable study.
`GET /api/v1/spatial/studies/{study_id}/candidates` returns the ranked candidates;
an empty candidate list is valid.

`POST /api/v1/spatial/studies/{study_id}/evaluate` requires the exact stored
baseline, candidate ID, and returned intervention. It reads the candidate's
precomputed Before/After graph comparison, verifies SIM v3 accepted that evaluated
candidate, and returns `execution:"stored_graph_comparison"` with
`sumo_executed:false`. It does not recalculate against changed inputs. All options
are computed from the same original snapshot and shared route sample when the
study is created.

The frontend labels fixture studies as synthetic and OSM studies as sourced
pedestrian graph analysis. Unknown cost, physical feasibility, traffic effects,
and missing feature coverage remain unknown. Optional evidence-grounded cloud AI
planning is documented in [AI_PLANNING_API.md](AI_PLANNING_API.md). It is disabled
until a server-side provider is configured and never supplies simulated impacts.

## Limits and errors

The worker runs one graph study at a time with a 90-second deadline. Requests
support 1–64 route samples, up to 3 returned and 6 evaluated candidates, candidate
pool limit 30, and route geometry limit 16. Clients should allow more than 90
seconds for uncached OSM acquisition. This is a synchronous API, not a background
job or SSE service. A disconnected client does not cancel the worker; the server
deadline still applies.

- `422`: malformed request or unsupported/invalid study area
- `404`: unknown study or candidate
- `409`: baseline/intervention mismatch or candidate not accepted by SIM validation
- `503`: engine unavailable or another study is running
- `504`: worker deadline exceeded; no fallback was run
- `502`: worker failure or incompatible engine response

Errors use the standard API error envelope. Run the project checks with
`uv run --locked pytest -q tests sim/test_engine.py` and
`uv run --locked python scripts/health_smoke.py`.
