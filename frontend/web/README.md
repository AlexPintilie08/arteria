# ARTERIA web application

This Next.js App Router application serves the ARTERIA presentation at `/` and
the product workspace at `/app`. The workspace includes the FastAPI-connected
synthetic signal-timing demo and the SIM v3 pedestrian graph panel with the
bundled Iași OSM neighborhood catalog.

## Run locally

Use Node.js 24.x. From the `frontend/` workspace root:

```bash
npm ci
npm run dev
```

Run the backend in another terminal from the repository root:

```bash
uv run --locked uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://localhost:3000/> or <http://localhost:3000/app>. The default API
base URL is `http://localhost:8000`, and the backend allows the local web origin.
Set optional public variables in `frontend/web/.env.local` and restart Next.js.
The map style URL is optional; the neutral canvas and bundled neighborhood
geometry work without a configured basemap.

## Data and limitations

The `/app` map loads all 24 sourced OSM polygon records and 7 point-only places.
Map clicks and search share the same selection; point-only places stay points,
and over-limit polygons explain that they need controlled analysis. OSM place
extents are not official administrative boundaries.

For an eligible polygon, **Rulează studiu pietonal SIM** calls the real
`POST /api/v1/spatial/studies` endpoint with its canonical SIM ID. The workspace
renders SIM urban problems and `problem_locations_geojson`, evidence-linked
solutions, and the backend's stored Before/After graph comparisons. AI planning
uses the stored study packet through the planning endpoints and displays only
SIM-validated recommendations. If the backend has no configured provider, the
UI keeps deterministic SIM results and states that cloud AI is unavailable.
The flow does not call the synthetic `/analyze` endpoint for sourced areas.

Studies may query OSM and take up to 90 seconds. Fresh clones do not include
ignored OSM caches; requests fail visibly and never fall back to fixtures. Use
the **Demonstrație semafoare** link or `/app/demo` to reach the original five
demo bookmarks and synthetic signal-timing experience. The marketing homepage
at `/` remains unchanged. Neither workflow claims observed traffic, SUMO
execution, population effects, or physical feasibility.

Run `npm run typecheck`, `npm test`, and `npm run build` from `frontend/`.
The complete project check is `bash scripts/check.sh` from the repository root.
