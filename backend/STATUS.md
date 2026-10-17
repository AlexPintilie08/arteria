# Backend status

## Working

- FastAPI application (`backend/main.py`) exposes `GET /health` and environment-backed local CORS.
- Five Python tests and real local HTTP health smoke pass on Windows and CI (Windows, macOS 15 ARM64, macOS 15 Intel).
- Node/uv-based setup and startup scripts (`scripts/setup.*`, `scripts/check.*`, `scripts/dev.*`) coordinate frontend and backend environments.
- Public HTTP/JSON API operational via `backend/server.py` on port 8000.
- Implemented and verified endpoints:
  - `GET /health` — health check and service metadata.
  - `POST /analyze` — area validation, mobility indicators, and detected candidate issues for Iași corridors (Podu Roș, Copou, Centru, Tătărași, Alexandru).
  - `POST /propose` — structured catalog-1 alternative proposals (minimal, moderate, transformative) with rationale, timeframe, and qualitative impacts.
  - `POST /evaluate` — comparative Before/After performance calculation with epistemic provenance.
- Full CORS support for local web (`http://localhost:3000`, `http://localhost:5173`) and LAN mobile clients.
- Complete API schema and payloads contract documented in `backend/API_ENDPOINTS.md` and detailed frontend-backend contracts in `api-specs/`.

## In Progress

- Connecting dynamic cloud LLM API with structured output validation for free-form proposal generation.
- Real-time OSMnx network graph extraction pipeline.

## Next

- Add configurable rate-limiting and authentication middleware.
- Expand intervention catalog validation rules for custom user-drawn polygons.
- Unify FastAPI routing with deterministic corridor models and SUMO runner bindings.

## Blockers

- None for the core evaluation workflow.
