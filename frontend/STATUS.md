# Frontend status

## Working

- The polished Next.js application preserves the marketing homepage and original synthetic signal-timing screens, with the five demo bookmarks available at `/app/demo`.
- The connected workspace uses the FastAPI endpoints for analysis, proposal, and evaluation; server IDs and returned results drive connected views. The original fixture experience remains available only in explicit demo mode.
- `/app` opens directly to the Iași MapLibre catalog with 24 sourced polygons and 7 point records, map/list selection, source uncertainty, SIM studies, problem geometry, evidence-linked solutions, validated AI planning, and stored graph comparisons.
- The connected study includes an intervention editor for detected problems, SIM-supported graph candidates, and the Minimală / Moderată / Transformatoare preference. The preference is stored locally and is not converted into a cost or impact claim; unsupported traffic and construction types stay conceptual or unavailable.
- The signal-timing API uses a deterministic synthetic model. Example corridor values remain synthetic and are not observed city measurements.
- Accessible controls, keyboard-operable map markers, focus indicators, reduced-motion behavior, Romanian localization, and responsive layouts are retained.

## Verification

TypeScript checks for all frontend workspaces and all 26 frontend tests pass. The web production build passes with the repo's Webpack build command. Browser QA completed a real OSM study, selected a returned problem, inspected a validated candidate, evaluated it, checked the AI provider status, and confirmed the demo and marketing routes. Backend pytest passes all 85 tests (one upstream Starlette/httpx deprecation warning). See [frontend/README.md](README.md) and [backend/FRONTEND_HANDOFF.md](../backend/FRONTEND_HANDOFF.md).

## Limitations

- Cloud AI uses the optional backend provider; when credentials are absent, the workspace reports provider unavailable and continues to display SIM results.
- The pedestrian graph workflow does not execute SUMO or provide calibrated traffic measurements.
- Expo mobile screens remain a scaffold and do not call the connected API.
