# Frontend status

## Working

- The polished Next.js application preserves the marketing homepage, MapLibre workspace, Three.js junction visualization, original analysis/scenario/comparison screens, and responsive design.
- The connected workspace uses the FastAPI endpoints for analysis, proposal, and evaluation; server IDs and returned results drive connected views. The original fixture experience remains available only in explicit demo mode.
- A separate pedestrian graph panel uses the optional spatial API. It labels fixture versus OSM sources and stored graph comparisons; it does not claim SUMO execution.
- The signal-timing API uses a deterministic synthetic model. Example corridor values remain synthetic and are not observed city measurements.
- Accessible controls, keyboard-operable map markers, focus indicators, reduced-motion behavior, Romanian localization, and responsive layouts are retained.

## Verification

The source backend/frontend branch reports passing TypeScript checks, frontend and backend tests, production build, and real-browser checks. Re-run the full project checks after branch integration and SIM v3 alignment; see [frontend/README.md](README.md) and [backend/FRONTEND_HANDOFF.md](../backend/FRONTEND_HANDOFF.md).

## In progress

- Restore the local SIM geography preview with 24 OSM Polygon/MultiPolygon place extents and 7 point-only records while keeping the five demo bookmarks separate.
- Connect SIM v3 proposal evidence to the graph-study UI only through a versioned backend adapter; until then, label graph previews and signal-timing demos according to their actual source.

## Limitations

- The browser does not call a cloud AI provider.
- The pedestrian graph workflow does not execute SUMO or provide calibrated traffic measurements.
- Expo mobile screens remain a scaffold and do not call the connected API.
