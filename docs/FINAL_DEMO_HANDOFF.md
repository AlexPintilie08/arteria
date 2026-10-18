# Final demonstration handoff

Presentation URL: **http://localhost:3000/app**. The same application serves the
synthetic signal-timing editor at `/app/demo` and the marketing page at `/`.

## Startup

Run these commands from the repository root in two PowerShell terminals, using
the already provisioned dependencies. Ensure the ports are free first; reuse a
healthy existing process instead of starting a competing server.

Backend, with a fresh/default local database:

```powershell
uv run --locked --no-sync uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

For the local presentation machine only, select its existing saved-study database
before the backend command:

```powershell
$env:ARTERIA_DB_PATH = 'backend/.data/integration-demo.sqlite'
```

The variable name is `ARTERIA_DB_PATH`. This database is ignored local runtime
data, remains uncommitted, and is not part of the submission. On another machine,
use the default database and the offline fixture action; saved study IDs below
only exist where that database is present. No cloud credential is needed.

Frontend, from the repository root:

```powershell
Set-Location -LiteralPath 'frontend/web'
node ../node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3000
```

Use the project's required Node 24 runtime. The frontend API default is
`http://localhost:8000`; backend CORS allows `http://localhost:3000` and
`http://127.0.0.1:3000`.

## Three-minute demonstration

1. Open `/app`. Click **Demo offline sintetic SIM**. This creates a small,
   deterministic synthetic graph study through the real backend/SIM pipeline and
   never downloads OpenStreetMap data.
2. Expand **Inspectează toate problemele detectate**, then inspect a problem and
   the intervention editor. Select an eligible SIM candidate and evaluate it.
   A conceptual recommendation without an approved candidate cannot be evaluated.
3. Inspect **Comparație Înainte / După** and its route table. Values come from SIM;
   zero, negative and unknown results must retain their actual meaning.
4. Show the provider status. With the current server configuration, planning
   reports `provider_unavailable`, `provider_disabled`, and `ai_generated: false`.
   Deterministic SIM recommendations are not cloud AI output.
5. Use **Demonstrație semafoare** to open the existing signal-timing editor in the
   same application. Its synthetic values are distinct from OSM graph results.

The fixture API was verified with three detected problems, twelve deterministic
solution records and three candidates. For the first approved candidate, the
shared sample has 15 pairs: four newly reachable, four unchanged and seven
unreachable in both states. Comparable-route distance savings are zero and the
percentage improvement is unknown (`null`). Reachability is a graph calculation,
not observed travel demand or a measured city benefit.

## Optional saved real OSM study

On the prepared presentation database, paste
`study_0fe7895e38e548dcab78a18f89f90d32` into **ID studiu salvat** and click
**Încarcă studiul salvat**. It is a Tătărași Nord walking-graph study for catalog
area `osm-w-670153116`, sourced from an OpenStreetMap snapshot retrieved on
2026-10-17. Loading by ID reuses stored results and does not reacquire OSM.
Preserve OpenStreetMap attribution and ODbL information. Catalog extents are OSM
place boundaries with uncertainty, not official administrative boundaries.

The approved saved candidate evaluates successfully with zero improved,
sixteen unchanged and zero regressed shared sample pairs. This older study has
no current AI planning evidence packet; requesting cloud planning is rejected.
The offline fixture provides the current problem/solution packet when needed.
Do not press **Rulează studiu pietonal SIM** during a network-independent pitch:
that separate real-data workflow may acquire live OSM data.

## Verified interpretation

- Stored OSM comparison: actual weighted pedestrian-graph calculations on the
  sourced snapshot; hypothetical candidate links have no physical approval.
- Offline fixture: synthetic graph and problems, calculated by the same SIM API.
- Signal timing: explicitly synthetic intersection model.
- Cloud AI: unavailable on the prepared server; no cloud request was made.
- SUMO: not executed by these backend/UI graph evaluations. Responses explicitly
  state `execution: stored_graph_comparison` and `sumo_executed: false`.

The existing local fixture study `study_05124bf43f47430e841c3f638d451155` can also
be loaded by ID on the prepared database. Creating a new fixture returns a new
study identifier while keeping the deterministic calculations reproducible.
