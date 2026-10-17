# Backend status

## Implemented

- FastAPI is the single authoritative server; legacy server.py launches it.
- Health, analyze, propose, evaluate, OpenAPI and CORS for ports 3000/5173.
- Frontend wire fields, structured uncertainty/provenance, geometry and constraints.
- Explicit demo bookmark contexts and unknown geographic-layer availability.
- Signal-timing catalog, exact optional tuning, adverse effects, immutable baseline.
- SQLite persistence, immutable retry results, retrieval endpoints and capacity errors.
- GET /api/v1/areas exposes demo bookmarks without fabricated boundary certification.
- SUMO requests fail explicitly; no cloud AI provider is claimed.

## Verification

`python3 -m uv run --locked pytest -q`: 60 tests passed, with one upstream
Starlette/httpx deprecation warning. Includes full flow, frontend shapes, persistence
across processes, concurrent retries, tuning, invalid geometry, CORS and provenance.

## Remaining integration

Frontend connected mode now calls the three core endpoints and the optional spatial
study/evaluation API. Browser checks passed for exact selection, tuning, resets,
errors without fallback and responsive layouts; see FRONTEND_HANDOFF.md.
Optional pedestrian graph API now runs the colleague's pinned engine snapshot through
a bounded subprocess. It preserves source evidence and immutable candidate comparisons
in SQLite. Offline fixture integration passed; actual OSM acquisition is implemented
but has not been exercised against the network. See SPATIAL_API.md.
No calibrated traffic engine, real city observations, auth, cloud AI or SUMO job/SSE API.
No changes to frontend/ or sim/ are required by this backend implementation.

A live HTTP flow, /docs, Next.js CORS and structural TypeScript checks against
frontend/shared/core/contracts.ts also passed. Request/response fixtures were
regenerated from the live server in docs/demo-flow.json.

Verified graph engine revision: `752c92da9184effc9b87704e0868320f569454ea`.
Tracked sim/ and frontend/ sources were not changed for this integration.

Current handoff and remaining work: [PREDARE_BACKEND.md](PREDARE_BACKEND.md).
The map preview is enabled locally via ignored `.env.local`; map/backend integration remains pending.
