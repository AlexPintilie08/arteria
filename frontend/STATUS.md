# Frontend status

## Working

- The polished Next.js application preserves the marketing homepage and original synthetic signal-timing screens, with the five demo bookmarks available at `/app/demo`.
- The connected workspace uses the FastAPI endpoints for analysis, proposal, and evaluation; server IDs and returned results drive connected views. The original fixture experience remains available only in explicit demo mode.
- `/app` opens directly to the Iași MapLibre catalog with 24 sourced polygons and 7 point records, map/list selection, source uncertainty, SIM studies, problem geometry, evidence-linked solutions, validated AI planning, and stored graph comparisons.
- The signal-timing API uses a deterministic synthetic model. Example corridor values remain synthetic and are not observed city measurements.
- Accessible controls, keyboard-operable map markers, focus indicators, reduced-motion behavior, Romanian localization, and responsive layouts are retained.

## Verification

TypeScript and frontend tests were run for this integration. The production build, backend regressions and real-browser end-to-end checks remain to be completed for this branch; see [frontend/README.md](README.md) and [backend/FRONTEND_HANDOFF.md](../backend/FRONTEND_HANDOFF.md).

## In progress

- Run end-to-end QA against a local backend and verify an available cached or live OSM area, including desktop and mobile layouts.

## Limitations

- Cloud AI uses the optional backend provider; when credentials are absent, the workspace reports provider unavailable and continues to display SIM results.
- The pedestrian graph workflow does not execute SUMO or provide calibrated traffic measurements.
- Expo mobile screens remain a scaffold and do not call the connected API.
