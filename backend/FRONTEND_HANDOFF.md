# Frontend handoff

Backend URL: `http://localhost:8000`. OpenAPI: `/docs` and `/openapi.json`.
The existing TypeScript wire shapes are supported for the three core endpoints,
within the explicitly synthetic signal-timing catalog. API_ENDPOINTS.md's
roundabouts, underpasses and sensor values are not supported operations/data.

Integration is now implemented in `ConnectedWorkspace.tsx` (default API mode).
The following checklist describes the implemented wire behavior. The original
fixture preview remains available only with `NEXT_PUBLIC_DEMO_MODE=true`.
The connected workspace includes a separate pedestrian graph panel and does not
use local traffic calculations. Steps for future client changes:

1. Set `NEXT_PUBLIC_DEMO_MODE=false` and `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
   in the Next.js environment and restart Next.js. This enables the connected analysis, proposal, evaluation and pedestrian panels.
2. Keep `analysis_id` and **`baseline_id`** from the response. Add `baseline_id: string`
   to the frontend `AnalyzeResponse` type; this additive backend field is required
   for comparisons and must never be fabricated from a date or area slug.
3. Select issues from `analysis.issues`, not `demoIssuesByNeighborhood`/`allDemoIssues`.
   The returned demo issue ID is `signal_balance`; fixture issue IDs will return 404.
4. Call `api.propose` with that analysis, issue and area reference. Render the returned
   alternatives, including limitations, validation and expected impacts.
5. Copy the selected alternative's `interventions` array unchanged into `api.evaluate`.
   Include `baseline_id`, `proposal_set_id`, `alternative_level`, and optionally
   `evaluation.indicators`. Use returned indicator IDs: `ns_delay`, `ew_delay`,
   `mean_delay`. Unknown indicator names return 422.
6. Display `comparisons`, `simulation` and warnings from the HTTP response. A minus
   delta is an improvement for delay; do not recalculate outcomes in the browser.

For a timing slider, request a fresh proposal with the additional field
`parameters: { ns_green_seconds: 55 }` and `requested_alternatives: ["minimal"]`.
Add this optional field to the client request type. Then evaluate its returned
intervention. CTP priority, lane width, roundabouts and underpasses are unsupported;
do not silently map them to green time. Altering the intervention after proposal
issuance returns 409.

Bookmark IDs from the existing analyze request (`preview-copou`, `preview-centru`,
`preview-podu-ros`, `preview-tatarasi`, `preview-alexandru`) are accepted as DEMO
contexts. They are not certified areas. GET `/api/v1/areas` supplies demo bookmarks,
with unknown bounds/population/sensors as null. Layers remain `unknown`.

Persisted result retrieval: GET `/analyses/{id}`, `/proposals/{id}`,
`/evaluations/{id}`. These are local-demo records, not authenticated per-user history.
The planned `/api/v1` auth/scenario CRUD/SUMO streaming APIs are not implemented.

## Map-first SIM and AI workflow

The product route `/app` now opens to the Iași MapLibre catalog. It loads the
24 canonical OSM polygon/multipolygon records and 7 point-only places; map clicks
and catalog search share the selected canonical SIM ID. Points never receive
fabricated boundaries, and polygons are explicitly described as mapped OSM place
extents rather than official administrative borders.

For eligible polygons the client calls `POST /api/v1/spatial/studies` with
`source: "osm"` and the selected `neighborhood_id`. It renders
`urban_issues.problems`, the returned `problem_locations_geojson`,
`solution_plan.solutions`, packet hash and source warnings. Only candidates with
`candidate_backed_evaluated` validation can reach the stored comparison route.
Before/After distances, outcomes and aggregate impacts are taken from SIM's
`POST /api/v1/spatial/studies/{study_id}/evaluate` response.

AI planning calls `POST /api/v1/spatial/studies/{study_id}/planning` with a
stable `Idempotency-Key`. Only `ai_generated: true` responses in a completed
status with SIM validation are shown. Candidate geometry and impact come from
`authoritative_sim_solution`; other results stay labeled as deterministic SIM
evidence. `GET /api/v1/spatial/studies/{study_id}/planning/{planning_id}` reloads
the persisted result. The UI reports provider unavailable when cloud credentials
are absent. The signal timing flow remains synthetic at `/app/demo`. Neither
workflow runs SUMO or reports observed traffic or physical feasibility.
