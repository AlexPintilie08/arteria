# ARTERIA Frontend Implementation Handoff

## Purpose and implementation order

Make the existing connected `/app` workspace the Iași map-first planning experience. Keep the current marketing page, Three.js concept scene, MapLibre implementation, connected analysis flows and five synthetic bookmarks. This document is for the frontend owners; backend HTTP orchestration belongs to `backend/`, and graph algorithms/evaluation belong to `sim/`.

Recommended order:

1. **P0-01:** put the connected MapLibre workspace and OSM catalog in the first `/app` view.
2. **P0-02:** render all 24 sourced polygons and 7 point records, with map-to-list and list-to-map selection.
3. **P0-03:** send only the selected canonical SIM catalog ID to the existing spatial study API.
4. **P0-04–07:** render returned evidence, honest candidate effects, useful comparison and accurate engine labels.
5. **P1-01:** polish responsive behavior, visual hierarchy, keyboard/touch interaction and Romanian copy.
6. **P2-01:** add map playback of real SUMO results only after backend and SIM provide a supported result contract.

Priority totals: **P0: 7 tasks; P1: 1 task; P2: 1 task.**

## Verified current baseline

The audited source commit is `60fe2eed4230ddeffe56bcedf44c49d66861b206`. The local QA audit reported 24/24 browser checks passed, 38 screenshots, 9 frontend tests passed, and passing TypeScript checks and production build. See the local audit report filenames `00_EXECUTIVE_SUMMARY.md`, `02_TEST_RESULTS.md`, and `03_VISUAL_AUDIT.md`; they and their screenshots live in the ignored `.qa/full-app-audit/` directory and are not published by this handoff.

Current architecture and observed behavior:

- `frontend/web/src/app/app/page.tsx` renders the workspace `App` from `frontend/web/src/features/workspace/Workspace.tsx`. `App` chooses `PreviewApp` only when `NEXT_PUBLIC_DEMO_MODE === 'true'`; otherwise it renders `ConnectedWorkspace`.
- `PreviewApp` already has a dynamic MapLibre map and a desktop map-plus-inspector layout. It uses synthetic fixture geometry and is not the connected SIM study flow. Do not fix the connected default by changing only `PreviewApp`.
- `ConnectedWorkspace.tsx` starts on its `analysis` section and renders a synthetic signal-timing form. Its other sections are scenarios, comparison and a separate `SpatialPanel` under “Acces pietonal.” The first view has no map.
- `SpatialPanel.tsx` already calls `spatialApi.spatialNeighborhoodStudy(selectedPlace.id)` for valid polygon selections and `spatialApi.spatialEvaluate(...)` for a returned, candidate-backed option. It owns its own place/study state, renders a map only after a place is selected, and does not share that map with the default analysis view.
- `NeighborhoodExplorer.tsx` fetches `frontend/web/public/data/iasi-neighborhoods.geojson` and `frontend/web/public/data/iasi-neighborhood-validation.json` only when its disclosure is opened. It offers accent-insensitive search and keyboard-operable list buttons. It does not draw the whole catalog.
- The static GeoJSON contains **31 records: 24 Polygon and 7 Point** in this snapshot. The loader and SIM accept MultiPolygon too. Validation marks 22 polygons valid and 2 as requiring controlled analysis; all 7 points are `point_only`.
- `sim-geography.ts` already validates finite WGS84 positions, Polygon/MultiPolygon rings and point positions, skips malformed records, preserves IDs, searches names/aliases/IDs without diacritics, calculates feature bounds, and builds controlled-analysis messages.
- `MapViewport.tsx` uses MapLibre 6 with an OSM raster base map and attribution. It currently renders the synthetic demo area/corridors and issue pins, then adds a `sim-place` GeoJSON source containing at most the one selected OSM polygon. It draws a selected point marker for one point record. It has no OSM polygon hover or click handler and receives no SIM study object or result layers.
- `frontend/shared/core/api.ts` already exposes `spatialStudy`, `spatialNeighborhoodStudy` and `spatialEvaluate`. The shared client currently exposes POST methods only; add a small GET helper if implementing the already-existing retrieval routes. The browser currently uses the bundled catalog; backend revalidates the canonical ID.
- The five existing synthetic bookmarks are UI/demo contexts, not certified neighborhood boundaries and not the OSM catalog IDs. Keep them separate and preserve their behavior.

Visual evidence from the local audit: `03_VISUAL_AUDIT.md` describes the cream editorial homepage and 3D concept, the dark connected form without an initial map, the separate OSM catalog, the zero-change Tătărași evaluation, and the narrow mobile comparison. Relevant local screenshot filenames are `landing-hero-threejs-1440.png`, `connected-analysis-empty.png`, `osm-catalog-loaded.png`, `osm-graph-evaluation.png`, and `signal-comparison-mobile.png` under the audit’s `screenshots/` folder. These are evidence descriptions, not links to files that will be present on GitHub.

## Shared frontend/backend flow

The implementation must preserve this single geography identity and lifecycle:

**Selected OSM polygon → canonical SIM `neighborhood_id` → spatial study → SIM candidate validation → stored-baseline evaluation → map layers and comparison.**

The static record’s ID is only a selection value; the backend resolves it again from the SIM catalog. Never send a display name, `preview-` bookmark ID, or client-generated boundary as the authoritative study area. Points and invalid/controlled polygons stay selectable for map navigation but must not be submitted as a standard analysis.

Current spatial API, implemented today:

```http
POST /api/v1/spatial/studies
Content-Type: application/json
```

```json
{
  "source": "osm",
  "neighborhood_id": "<canonical SIM catalog ID>",
  "sample_count": 16,
  "max_candidates": 3,
  "seed": "arteria-spatial-v1"
}
```

The request fields and limits come from `backend/spatial_models.py`: `source` is `fixture` or `osm`; an OSM request requires a 1–200 character `neighborhood_id`; `sample_count` is an integer from 1 through 64; `max_candidates` is an integer from 1 through 3; and `seed` is 1–100 characters. The existing frontend helper sends only `source` and `neighborhood_id`, so the server supplies the defaults above.

The successful response is a persisted `Study` with `study_id`, `baseline_id`, `created_at`, `source`, `engine_revision`, `calculation: "pedestrian_graph"`, `analysis`, `alternatives`, `proposal_options`, `proposal_validation`, `evidence_packet`, and `warnings`. The nested `analysis` includes the SIM `analysis_id`, `area`, `indicators`, `issues`, `issue_geojson`, `heatmaps`, `layer_availability`, `layers`, `networks`, `network_metrics`, `provenance`, `uncertainty`, and `warnings`. GeoJSON positions are `[longitude, latitude]` in EPSG:4326. These fields come from `backend/spatial_models.py`, `backend/engine_contract.py` and `sim/analysis.py`.

Current retrieval and evaluation endpoints:

- `GET /api/v1/spatial/studies/{study_id}` retrieves the immutable stored study.
- `GET /api/v1/spatial/studies/{study_id}/candidates` retrieves its candidate list and warnings.
- `POST /api/v1/spatial/studies/{study_id}/evaluate` accepts `baseline_id`, `candidate_id`, and the exact server-returned `intervention`. The server rejects a different baseline, unknown candidate, changed intervention, or candidate not marked `candidate_backed_evaluated`.
- `SpatialEvaluation.execution` is `stored_graph_comparison` and `sumo_executed` is always `false` for this route.

The same flow in compact response form (angle-bracket values are placeholders; omitted optional nested details are omitted deliberately):

```json
{
  "study_id": "<stored study ID>",
  "baseline_id": "<immutable baseline ID>",
  "source": "osm",
  "engine_revision": "<SIM revision>",
  "calculation": "pedestrian_graph",
  "analysis": {
    "area": {"city_id": "iasi-ro", "area_id": "<canonical SIM catalog ID>", "crs": "EPSG:4326"},
    "indicators": [{"id": "<SIM indicator>", "value": null, "unit": "<unit>", "status": "unknown"}],
    "issue_geojson": {"type": "FeatureCollection", "features": []},
    "layers": {"<SIM layer name>": {"type": "FeatureCollection", "features": []}},
    "networks": {"walk": {"type": "FeatureCollection", "features": []}},
    "layer_availability": {"<layer>": {"status": "unknown"}},
    "provenance": {"source": "OpenStreetMap", "retrieved_at": "<source timestamp>"}
  },
  "alternatives": {"ranked_candidates": []},
  "proposal_options": [],
  "proposal_validation": {"status": "<SIM status>", "summary": {"accepted_count": 0, "rejected_count": 0}, "results": []},
  "warnings": []
}
```

No current endpoint generates an LLM recommendation or runs SUMO. The signal `/analyze`, `/propose`, and `/evaluate` endpoints are a separate deterministic synthetic intersection demo. They do not analyze the selected OSM neighborhood.

The compact JSON excerpt above is illustrative rather than a complete response object: it elides the required `analysis.area.boundary` payload and other nested properties. Do not use it as a fixture without supplying the actual schema fields.

## P0 — Mandatory for the hackathon MVP

### P0-01 — Make the connected `/app` a map-first workspace

**Current behavior:** the default non-preview route renders `ConnectedWorkspace` with a signal form. The real OSM map is only in the separate spatial tab, and appears after selecting a place. The polished homepage at `/` is a distinct visual surface.

**Desired behavior:** opening `/app` immediately shows an Iași MapLibre canvas with the OSM catalog, neighborhood selection and an adjacent inspector. The user can start a supported SIM study from that selection. The synthetic signal flow remains accessible in a clearly labeled “Semaforizare demo” mode.

**Reuse and likely files:** `Workspace.tsx`, `ConnectedWorkspace.tsx`, `SpatialPanel.tsx`, `MapViewport.tsx`, `NeighborhoodExplorer.tsx`, `ConnectedWorkspace.module.css`, `frontend/web/src/app/globals.css`. Keep the marketing route `frontend/web/src/app/page.tsx` and its Three.js components unchanged.

**Implementation steps:**

1. Move or lift catalog load, selected canonical place ID, active study, evaluation, request state and active map-layer state into one connected workspace owner. Prefer an extracted map-planning component if it keeps the existing signal screen manageable.
2. Compose the existing MapLibre canvas, the existing explorer/list, a selected-place inspector and SIM results in the default planning section. Avoid mounting a second map for the same selected area.
3. Keep the signal-analysis, scenarios and comparison components reachable from a distinct demo navigation item or mode. Show that bookmark IDs are demo contexts and never use them as OSM `neighborhood_id` values.
4. Keep the map mounted and selected place visible while loading, on API errors, and when switching result tabs. Present errors in the inspector without replacing the map.
5. Preserve the existing marketing page, route paths, app navigation, OSM attribution and boundary caveat.

**Acceptance:** `/app` opens with a loaded Iași map and discoverable search/catalog; the selected polygon and study remain visible through evaluation; existing navigation and five bookmarks still work; loading and errors do not collapse the map; no traffic measurement is implied.

**Tests:** visit `/app` at 1440×900 and 390×844; verify the map is visible before user action, catalog is not hidden behind a separate synthetic page, signal demo remains accessible, browser console has no blocking error, and map/inspector retain their layout during delayed, rejected and failed study responses.

**Risks:** changing only the current preview path leaves the real connected default unchanged. Duplicating the map or selection state in `ConnectedWorkspace` and `SpatialPanel` can make the list and map disagree.

**Definition of done:** one connected workspace owns one selected SIM place and one map; the initial route is geographic; the signal demo stays separate and honest; tests above pass.

**Effort:** 3–4 hours.

### P0-02 — Draw the full sourced catalog and select polygons on the map

**Current behavior:** the two bundled files at `frontend/web/public/data/iasi-neighborhoods.geojson` and `frontend/web/public/data/iasi-neighborhood-validation.json` contain 24 polygons and 7 points. The explorer loads them only when opened. `MapViewport` shows only the currently selected polygon and has no polygon click/hover interaction.

**Desired behavior:** load the checked catalog during initial workspace setup and draw all valid Polygon/MultiPolygon records at once. Keep all seven point-only records as point markers, never as polygon features. A user can click a polygon, search/select from the list, or choose a point marker; each action updates one canonical selected ID and the visible inspector.

**Reuse and likely files:** `NeighborhoodExplorer.tsx`, `sim-geography.ts` (`loadSimCatalog`, `isSupportedSimGeometry`, `searchSimPlaces`, `featureBounds`, `placeCenter`), `MapViewport.tsx`, and `frontend/web/tests/sim-geography.test.ts`.

**Implementation steps:**

1. Load both static files once when the connected map workspace mounts. Keep retryable loading and error states. Reuse `loadSimCatalog` as the parsing/geometry gate and preserve `skippedCount`; do not silently fabricate or repair geometry.
2. Normalize each record into a render feature with a stable `catalog_id` copied from its canonical catalog ID, preserving all original SIM/OSM properties. Keep a lookup from `catalog_id` to `SourcedPlace` and its validation record.
3. Create one GeoJSON source for the full normalized catalog. Add polygon fill/outline layers filtered to Polygon/MultiPolygon and a separate circle/symbol layer filtered to Point. Do not make 31 sources/layers. Keep result layers as separate sources only when actual analysis results exist.
4. Set a stable promoted feature ID (`catalog_id`) before using MapLibre feature state. Attach `mousemove`/`mouseleave`/`click` handlers once after the map is ready; update hover state and selected state without registering a new handler on each React render. Remove handlers and map-owned listeners on unmount.
5. Sort polygon rendering deterministically: render larger finite `validation.area_km2` extents before smaller ones; use canonical ID as the stable tie-breaker, and sort records with unknown area by canonical ID after known areas. A direct click selects the topmost rendered polygon; list/search selection always selects the exact requested canonical ID. This gives predictable behavior in overlaps and a way to choose any overlapped record from the list.
6. On polygon selection, update the shared selection, highlight it, fit to `featureBounds` with padding and a max zoom, show the name in a popup or inspector, and set the matching list button as pressed. On point selection, use `placeCenter`/the point coordinates and `flyTo`; do not create a boundary source for it.
7. Search remains accent-insensitive. Selecting a search result updates the same map state. Filtering the list must not clear the selection or remove the selected feature. Clearing the selection clears only the selected state; all 24 polygons and 7 points remain visible.
8. Style source extents as OSM place extents, not legal neighborhood limits. Keep attribution `© OpenStreetMap contributors`, ODbL-1.0 and the partial-coverage warning visible. Use a restrained translucent fill, high-contrast outline, distinct hover/selected state and a readable legend.

**Acceptance:** all 24 polygon geometries render simultaneously; all 7 Point geometries render as points; every feature retains the exact catalog ID; click→list, list→map and search→map work; selected bounds are fitted; clear/filter/zoom do not lose identity; invalid records are skipped and counted; no official-boundary claim is added.

**Tests:** extend `frontend/web/tests/sim-geography.test.ts` for Polygon/MultiPolygon normalization, unique catalog IDs, malformed geometry, exact-ID selection after filtering, bounds, point preservation and deterministic overlap priority. In a browser, click two visible polygons, hover a polygon, select a search result, zoom, filter, select an overlapped record from the list, tap a point on a touch viewport, and confirm there is no Polygon layer feature for any point record.

**Risks:** MapLibre feature state needs unique source feature IDs; source feature `id` alone should not be assumed until normalized and checked. Polygon overlap makes map clicks ambiguous unless the priority rule above is implemented. Avoid unsafe assumptions about source properties: `sim-geography.ts` already has an ID fallback for point records.

**Definition of done:** one map source owns the complete sourced catalog; list, search, point markers and map clicks use the same canonical ID; invalid and point records remain safe.

**Effort:** 4–6 hours.

### P0-03 — Connect selection to the existing SIM study/evaluation flow

**Current behavior:** `SpatialPanel` already sends `POST /api/v1/spatial/studies` using `selectedPlace.id` and server defaults, but owns selection in the separate spatial section. Its study button is enabled only for a non-Point record with validation status `valid`.

**Desired behavior:** the integrated inspector’s “Analizează zona” action sends the selected record’s canonical ID through the existing `spatialApi.spatialNeighborhoodStudy`. The map remains active while the server loads or returns a structured error.

**Reuse and likely files:** `SpatialPanel.tsx`, `ConnectedWorkspace.tsx`, `frontend/shared/core/api.ts`, `frontend/shared/core/contracts.ts`, `sim-geography.ts`.

**Implementation steps:**

1. Make the selected place a shared controlled value (or shared hook) so map, search, list, analysis, candidates and result layers cannot each hold a different selected place.
2. Enable study only when the selected geometry is Polygon/MultiPolygon and bundled validation says `analysis_eligible === true` / `status === 'valid'`. Keep the backend check authoritative; do not let the browser pass an arbitrary polygon as the analysis boundary.
3. Send `{"source":"osm","neighborhood_id":"<canonical id>"}` to the current POST endpoint. Do not send a bookmark ID, label, client-created ID, or the entire geometry.
4. Preserve the static `sample_count`, `max_candidates` and `seed` defaults unless there is an explicit product setting. If exposing these inputs, constrain them to the current Pydantic limits.
5. Use `AbortController` and a request generation token: when the user switches place or starts a newer request, cancel the browser request and discard any late response for the old place. Clear the old study/evaluation immediately so they cannot be mistaken for the new area. Aborting fetch does not guarantee that the synchronous server subprocess has stopped; do not show a false cancellation guarantee.
6. Map API errors from the current structured envelope: `unknown_neighborhood` (404), `study_area_rejected` (422), `spatial_failure` (502), `spatial_unavailable` (503), and `spatial_timeout` (504). Show a short Romanian recovery message and optional details. Never fall back to the synthetic fixture on any failed OSM study.
7. Use current stored retrieval routes when adding refresh/reopen behavior: `GET /api/v1/spatial/studies/{study_id}` and `GET /api/v1/spatial/studies/{study_id}/candidates`. Do not introduce a duplicate catalog API for the MVP.

**Acceptance:** valid polygon selection makes one request with the exact canonical ID; point, invalid and over-limit selections do not submit; source acquisition errors show an error and no synthetic result; changing place cannot display a late stale study; the successful study ID and baseline ID remain tied to the selected area.

**Tests:** mock API cases for 201, 404 unknown ID, 422 point/over-limit, 502 acquisition failure, 503 busy/unavailable and 504 timeout; assert no fixture call occurs after an OSM failure. In a browser, start a slow request, switch neighborhoods, and verify the old result is ignored while the map stays navigable.

**Risks:** the browser can abort its fetch but the current backend runs an in-process synchronous route and a subprocess with a 90-second timeout; server-side work may finish after the UI has switched. Use a request token for UI correctness and leave true job cancellation for a future job API.

**Definition of done:** only an eligible canonical place can start an OSM SIM study; loading/error/empty states retain map and selection; no fallback or stale result is presented.

**Effort:** 2–3 hours.

### P0-04 — Render SIM findings and graph data on the map

**Current behavior:** the study response is stored in `SpatialPanel`, but `MapViewport` receives only a selected place, fill toggle and a status string. It does not render the study’s returned graph, issue, layer or heatmap FeatureCollections.

**Desired behavior:** present useful network analysis and candidate geometry in the same geographic view, using only features the backend actually returned.

**Reuse and likely files:** `MapViewport.tsx`, `SpatialPanel.tsx`, `frontend/shared/core/contracts.ts`, `ConnectedWorkspace.module.css`.

**Implementation steps:**

1. Align `frontend/shared/core/contracts.ts` with the stored backend response before adding typed props: the current `SpatialStudy` type omits backend-returned `created_at` and `calculation`. Add typed props or a typed layer model for the selected `SpatialStudy` and, separately, the returned `SpatialEvaluation`. Keep the map a renderer; keep request lifecycle and result selection in the workspace.
2. Draw `analysis.networks.walk` (and another mode only if returned) as the pedestrian graph. Use `analysis.issue_geojson` or an issue’s actual `geometry` for detected issue features. Ignore a missing/null/empty collection safely.
3. Draw returned candidate `geometry` or its exact supported `intervention` geometry as a hypothetical connection layer. Do not infer a route from issue text or from random coordinates.
4. Use `analysis.layers` and `analysis.heatmaps` only when the corresponding `layer_availability` and returned collection support rendering. A missing or `unknown` layer is a legend/status item, not an empty map layer interpreted as “no issues.”
5. Add layer toggles and a visible legend for neighborhoods, walking graph, calculated issues, hypothetical candidates and any actual before/after geometry. Distinguish source OSM geometry, calculated SIM output, synthetic fixture output, estimates and unknowns by both text and styling.
6. Keep selected neighborhood boundaries and OSM attribution visible above/below result layers. Use bounded GeoJSON and avoid rebuilding a MapLibre source for each React render; update existing sources with `setData` and clean up once.
7. Current candidate route records expose node IDs, outcomes and distance deltas, but do not define a route-line geometry in `SpatialEvaluation.impact.routes`. Do not draw a before/after path until a returned GeoJSON route layer exists. If route lines are required for the MVP, request that exact output from the SIM owner and add it to the backend contract first.

**Acceptance:** the map renders exactly the returned walking graph, issue geometries and candidate link geometry; absent/unknown geometry renders no invented markers; toggles and legend reflect actual availability; changing place/study removes old result layers but keeps all catalog polygons.

**Tests:** use fixtures for empty, valid, malformed, Point, LineString and FeatureCollection result payloads; malformed features must not crash the map; verify source/feature counts against API payloads and verify an unknown layer does not become “zero issues.” Browser-check layer toggles and changing study IDs.

**Risks:** result GeoJSON may grow substantially after feature acquisition; render only actual bounded returned collections and make limits visible. Issue geometries are calculated screen signals, not field-observed incidents.

**Definition of done:** study output is visually inspectable, data-driven and honest about missing or unsupported geometry.

**Effort:** 3–5 hours.

### P0-05 — Rank and explain candidate options without overstating benefit

**Current behavior:** `SpatialPanel` filters options to `candidate_backed_evaluated`, then shows route sample count and improved/regressed counts. The tested Tătărași Nord options all changed 0 of 16 shared sampled pairs; the zero result is not emphasized until comparison. SIM also returns candidate-local targeted diagnostics, which are not the common ranking sample.

**Desired behavior:** a judge can quickly see what the candidate changes in the graph, where it is, whether SIM accepted it, the shared sample effect and what remains unknown.

**Reuse and likely files:** `SpatialPanel.tsx`, `frontend/shared/core/contracts.ts`, `presentation.ts`.

**Implementation steps:**

1. Join `proposal_options` with `proposal_validation.results` by exact `candidate_id`. Show rejected options in a distinct explanation state if useful, but never make them selectable for evaluation.
2. Before the compare button, show shared-sample `evaluated_pair_count`, `improved_count`, `regressed_count`, `newly_reachable_count`, `newly_unreachable_count`, and `total_distance_savings_m` using returned values and units.
3. If shared-sample improved/newly reachable counts and distance savings are all zero, visibly label it “No measurable change in this shared sample.” Do not hide the candidate, round a null to zero, or write an improvement claim.
4. If `targeted_diagnostic_sample` exists, show it separately under a label such as “Local diagnostic, not the shared ranking sample.” Never add its counts to shared-sample totals or use it as an equivalent ranking statistic.
5. Display validation state, candidate ID, returned `summary`, screening warnings, source, source-area verification, and `physical_feasibility: unknown`. Keep costs and construction feasibility as unknown/unsupported.
6. State clearly that the sample consists of modeled graph-node pairs, not observed resident trips or pedestrian counts.

**Acceptance:** no-op candidates are clearly marked before evaluation; UI totals come from the shared sample; local diagnostics remain separate; rejected options cannot be selected; no cost/safety/buildability/benefit claim is invented.

**Tests:** a positive synthetic fixture candidate shows its returned 4 newly reachable of 15 pairs as fixture evidence; a real OSM no-op shows zero change across the returned sample; null totals stay unknown; a rejected candidate has no enabled compare action; targeted metrics never alter shared totals.

**Risks:** sorting by the candidate-local probe can turn an explanatory diagnostic into misleading population-wide benefit. Keep the SIM shared-sample ranking authoritative.

**Definition of done:** candidate validity and modeled effect are understandable before the user requests comparison; all statements map to response fields.

**Effort:** 1.5–2.5 hours.

### P0-06 — Make Before/After comparison legible and method-aware

**Current behavior:** desktop signal comparison is a table. At 390 px it remains within the viewport, but indicator names, units and values break into narrow fragments. SIM comparison shows aggregate route counts and per-pair outcomes but is also a long vertical section.

**Desired behavior:** baseline and evaluated scenario are visibly paired, with units, direction and method. Mobile users can read every number without zooming or fragmented words.

**Reuse and likely files:** `ConnectedWorkspace.tsx`, `SpatialPanel.tsx`, `ConnectedWorkspace.module.css`, `frontend/shared/core/contracts.ts`.

**Implementation steps:**

1. Label the baseline ID, candidate/intervention and scenario ID; show source, method, engine revision and validation status.
2. For each returned SIM aggregate, include `evaluated_pair_count`, improved/regressed/newly reachable/newly unreachable counts and distance-savings units. Mark `null` as “unknown/not comparable,” not zero.
3. Explain that graph distances and sampled node pairs are calculated model outputs; signal values are deterministic synthetic delay estimates; neither is observed traffic. Show simulation status from the response.
4. Use responsive stacked comparison cards on narrow screens (recommended) or a table with a clear, keyboard-accessible horizontal-scroll affordance and minimum readable column width. Preserve semantic labels for screen readers.
5. Show map overlays or side-by-side maps only for actual returned geometry. Current evaluation route rows do not provide route polylines.

**Acceptance:** each value has its indicator label and unit; positive/negative meaning is explained for that indicator; unchanged and unknown values have distinct states; the 390 px comparison is readable without horizontal document overflow or broken numeric fragments.

**Tests:** test improved, worsened, unchanged, null and missing-unit cases; test 390 px and tablet layouts; verify focus order and screen-reader labels; confirm simulation method and source stay visible.

**Risks:** one global “green is good/red is bad” rule is wrong for some indicators; encode direction semantics per indicator, and do not color null data as a result.

**Definition of done:** desktop and mobile comparison state identifies what was compared, how it was calculated and what the available data cannot say.

**Effort:** 2–3 hours.

### P0-07 — Distinguish SIM, AI, synthetic estimates and SUMO status

**Current behavior:** the connected header says “Semaforizare demo · graf pietonal SIM v3.” The `/propose` signal alternatives are deterministic, SIM graph candidates are deterministic and no LLM is connected. Spatial evaluations always return `execution: "stored_graph_comparison"` and `sumo_executed: false`. The signal API’s SUMO request returns unavailable without fallback.

**Desired behavior:** a first-time user can tell which engine produced every result and whether AI or microscopic traffic simulation actually ran.

**Reuse and likely files:** `ConnectedWorkspace.tsx`, `SpatialPanel.tsx`, `presentation.ts`, `frontend/shared/core/contracts.ts`.

**Implementation steps:**

1. Add a compact mode/provenance/status strip for each result: “SIM NetworkX pedestrian graph,” “synthetic signal estimate,” “deterministic SIM candidate,” “AI not configured/not called,” and “SUMO not run/unavailable/completed” as supported by response data.
2. Treat current `source`, `engine_revision`, `calculation`, `execution`, `sumo_executed`, warnings and provenance as factual inputs. Do not infer AI or simulator completion from a button click, loading state or proposal text.
3. Reserve “observed” for source evidence explicitly marked observed; use “calculated,” “estimated,” “synthetic,” or “unknown” as appropriate. Keep OSM extents identified as partial mapped places, not official administrative boundaries.
4. If the proposed AI API is unavailable, present the existing SIM candidates as deterministic and keep them usable. Do not label a deterministic fallback “AI.”

**Acceptance:** no screen presents a synthetic signal estimate as Iași measurement, a graph comparison as observed journeys, a candidate as constructible, or a non-executed SUMO/LLM run as successful.

**Tests:** snapshot/test the labels for fixture, OSM, LLM unavailable, SUMO unavailable, SUMO completed and empty/unknown data. Simulate provider errors and verify no “AI result” label appears.

**Risks:** labels can become stale if hardcoded instead of derived from API status fields. Keep capability status in the typed response/presentation layer.

**Definition of done:** source, method, uncertainty and execution status are visible next to their result, including failure and unknown states.

**Effort:** 1–2 hours.

## P1 — Visual polish and responsive quality

### P1-01 — Unify the design and finish accessible responsive behavior

Keep the marketing page’s cream/ink palette, restrained navy accents, strong type hierarchy and Three.js scene. The connected workspace currently uses a separate dark form/card surface; the local audit screenshots `landing-hero-threejs-1440.png` and `connected-analysis-empty.png` show the visual break. Use a shared header, typography scale, status badges, spacing and navigation cues while keeping the map the dominant work surface.

Likely files: `frontend/web/src/features/workspace/ConnectedWorkspace.module.css`, `frontend/web/src/app/globals.css`, `frontend/web/src/app/page.module.css`, `MapViewport.tsx`, `NeighborhoodExplorer.tsx`.

Acceptance: desktop uses a map-led split (target roughly 65–70% map and 30–35% inspector where space permits); mobile presents a usable map-first canvas with an accessible bottom/stacked inspector; every action has visible focus; touch selection works without hover; Romanian labels are consistent; attribution and uncertainty remain readable; no horizontal page overflow at 390 px.

Tests: responsive browser pass at 1440×900, 768×1024 and 390×844; keyboard-only search/list/selection; focus visibility and contrast; check screenshot captures locally (keep them out of tracked source unless requested).

Effort: 2–4 hours.

## P2 — Post-hackathon

### P2-01 — Optional map playback of real SUMO scenario outputs

Only after backend exposes a real, versioned run/result contract and SIM supports the requested driving-network scenario. The current pedestrian study cannot be converted to a SUMO road network, and current `run_real_area_simulation` is not a candidate comparison. Render returned `GeoJSON` and actual trip metrics only; distinguish completed, unfinished and not-departed trips and synthetic demand. Do not fabricate route lines or progress.

Likely files: `MapViewport.tsx`, `SpatialPanel.tsx`, `frontend/shared/core/contracts.ts`. This is blocked on the backend and SIM contracts, not a frontend-only task.

Acceptance: map layers and before/after data are tied to run IDs, source/network revisions, seed, demand and execution status; unavailable data stays unavailable; mobile and accessibility checks pass.

Effort: 2–4 hours after backend/SIM support.

## Frontend verification checklist

Use the existing frontend workspace commands from `frontend/`:

```sh
npm test
npm run typecheck
npm run build
```

The current automated suite uses Node’s built-in test runner and includes `frontend/web/tests/sim-geography.test.ts`; it does not include a checked-in Playwright dependency or map-interaction E2E suite. Keep unit tests dependency-free where possible and perform the browser interaction checks below in the team’s available browser harness.

- [ ] `/app` opens on the connected Iași map, not the synthetic signal form.
- [ ] All 24 Polygon/MultiPolygon and 7 Point catalog records load from the two existing static data files; all canonical IDs remain unique and unchanged.
- [ ] No invalid geometry crashes catalog loading or map rendering; it is skipped and reported.
- [ ] Every valid polygon is drawn at once and can be selected with a pointer; hover/focus state is visible and selection still works after zoom.
- [ ] Click on map updates the exact list selection; list and search selection update map highlight and bounds; selection persists when the list is filtered.
- [ ] Point records remain Point features/markers and cannot trigger a zone study.
- [ ] Păcurari and Zona Industrială remain gated under default SIM limits; navigation stays usable.
- [ ] Study request body uses the selected canonical ID. Stale/canceled responses cannot overwrite a newer selection.
- [ ] OSM failure never falls back to a synthetic study.
- [ ] Map layers match the actual study GeoJSON; unknown/missing data never becomes a fabricated marker or zero.
- [ ] Tătărași Nord options with zero shared-sample effect are labeled no measurable change; targeted local diagnostic counts remain separate.
- [ ] Before/After comparison is readable on desktop and 390 px mobile; keyboard/touch access works.
- [ ] AI, SIM, synthetic estimate and SUMO states match actual API responses; no fake AI activity or SUMO progress appears.
- [ ] Existing five bookmarks, marketing `/`, Three.js controls and route navigation still work.
- [ ] No blocking browser console/page errors occur in a stable run; OSM raster tile abort noise during rapid pan should be distinguished from application errors.

## SIM v4 contract integration addendum (branch pending merge)

The SIM-owned changes on `feat/sim-v4-mvp` define [the v4 Python/result contract](../sim/INTEGRATION_CONTRACT_V4.md). This is not yet part of `main`; consume it only after the SIM PR is merged and the backend exposes the fields.

- Render candidate, issue, endpoint, shared-sample route, and separately labeled targeted-diagnostic GeoJSON only as calculated map evidence. Shared-sample impact is the ranking evidence; a local diagnostic improvement alone must be labeled `candidate_local_diagnostic_improvement_only`.
- Use `shared_sample_outcome_status`, `impact_evidence_status`, and `geographic_evidence_status` to distinguish no common-sample benefit, local-only diagnostic improvement, common-sample improvement/regression, mixed effects, and incomplete obstacle data. Do not convert zero, unknown, or unverified values to positive recommendation language.
- Feature-layer UI may request only `buildings`, `schools`, `healthcare`, `services`, `public_transport`, `parking`, `green_space`, and `crossings` via the backend. Preserve category availability states and OSM attribution/ODbL.
- Show SUMO data only when a paired result is `completed`; display run IDs, source/network revision, seed, synthetic demand, finished/unfinished/not-departed/unreported counts, actual TripInfo metrics, and returned network/changed-edge/vehroute GeoJSON. Mark vehroute geometry as SUMO edge-route geometry, never GPS telemetry. Keep synthetic-demand outputs separate from measured traffic.

Frontend acceptance and browser checks above remain required after backend wiring; SIM's Python implementation does not complete them.
