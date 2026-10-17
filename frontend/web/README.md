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

The 24 sourced OSM polygon records and 7 point-only records are bundled for
catalog browsing. OSM graph studies require internet access; fresh clones do not
include ignored OSM caches. OSM place extents are not official administrative
boundaries. The graph panel analyzes walking networks and evaluates graph
comparisons; it does not run SUMO or claim physical feasibility. Signal-timing
results are explicitly synthetic, and cloud AI generation is not connected.

Run `npm run typecheck`, `npm test`, and `npm run build` from `frontend/`.
The complete project check is `bash scripts/check.sh` from the repository root.
