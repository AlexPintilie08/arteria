# Backend status

## Implemented

- FastAPI is the single authoritative server; legacy `server.py` launches it.
- Health, analyze, propose, evaluate, OpenAPI, and CORS for the supported frontend origins.
- Pydantic contracts, structured errors, provenance, uncertainty, geometry, and constraints.
- SQLite persistence with immutable records, retrieval endpoints, capacity errors, and backward-compatible spatial studies.
- Optional pedestrian graph studies from the SIM Iași catalog; failed OSM acquisition never falls back to a fixture.
- Spatial studies persist urban problems, evidence-linked solution plans, problem GeoJSON, the immutable AI packet, and its SIM integrity hash.
- Optional cloud AI planning through the OpenAI Responses API with strict structured output, SIM-owned response validation, bounded timeouts, result persistence, and optional idempotency keys. It is disabled by default and requires server-side credentials.
- Existing synthetic signal-timing demo remains explicitly synthetic. It does not become an AI or SUMO result.

## Verification — 2026-10-18

Using the already provisioned Python 3.12 environment without installing
dependencies:

```text
python -m pytest -q tests sim/test_engine.py sim/test_urban_intelligence.py
212 passed, including 21 backend AI planning tests; 1 upstream Starlette/httpx
deprecation warning
```

A real OSM study for catalog area `osm-w-670153116` reused a locally cached,
geometry-matching pedestrian graph and completed one bounded feature acquisition.
It persisted 12 SIM problems, 17 evidence-linked solutions, 23 problem GeoJSON
features, OpenStreetMap attribution, ODbL-1.0, verified area geometry, and a
matching packet hash. Planning on that stored study returned
`provider_unavailable` with `ai_generated: false`; the study remained retrievable.

**Live cloud smoke: `LIVE CLOUD AI BLOCKED — PROVIDER CREDENTIALS REQUIRED`.**
The runtime has no configured AI API key and AI is disabled by default. Provider
request behavior, failures, schema validation, and persistence were exercised
with deterministic mocks; no cloud request was made.

## Remaining limits

- The local cached driving graph found during verification was not equivalent to
  the current Iași study area, and SIM produced no driving interventions for it.
  No backend SUMO bridge was added.
- No calibrated traffic model, city telemetry, certified boundaries, physical
  feasibility validation, authentication/per-user isolation, SUMO jobs/SSE, or
  cloud database is provided.
- Real-area OSM coverage depends on the selected snapshot and is not a statement
  of population or observed travel behavior.

Frontend integration: [AI_PLANNING_API.md](AI_PLANNING_API.md) and
[SPATIAL_API.md](SPATIAL_API.md).
