# Implemented frontend contract (v0.3)

Base URL `http://localhost:8000`; JSON bodies. `/docs` is interactive and
`/openapi.json` documents typed request, response and error models.
See [frontend handoff](../backend/FRONTEND_HANDOFF.md) for exact client wiring changes.

| Method | Endpoint | Behavior |
| --- | --- | --- |
| GET | `/health` | Unchanged liveness response |
| POST | `/analyze` | Stable analysis/baseline IDs and synthetic indicators |
| POST | `/propose` | Validated signal-timing alternatives |
| POST | `/evaluate` | Exact selected intervention vs immutable baseline |
| GET | `/analyses/{id}` | Retrieve saved analysis |
| GET | `/proposals/{id}` | Retrieve saved proposal |
| GET | `/evaluations/{id}` | Retrieve saved evaluation |
| GET | `/api/v1/areas` | Demo bookmarks; unavailable bounds/sensors are null |

Minimal analyze request: `{"area":{"area_id":"iasi-demo-intersection"}}`.
The full frontend request with `area`, `layers`, `analysis.network_modes`,
`analysis.accessibility_thresholds`, and `data_as_of:null` is also accepted.
Supported area IDs and limitations are in backend/README.md. Geographic layers are
unknown; `mode` defaults to `demo`, with synthetic inputs. Non-null `data_as_of`
returns 422. `mode:"sumo"` returns 503, never demo fallback.

Optional baseline `inputs`: cycle_seconds (60–180, default 90), ns_green_seconds
(default 40), lost_seconds (10 only), ns_demand_vph (100–1500, default 700),
ew_demand_vph (100–1500, default 500). Both phases require at least 10 seconds green.

Propose requires `analysis_id`; optional fields: area reference, issue_id (use the
returned issue), intervention_catalog_version (`catalog-1`), constraints with
`max_affected_area:{value:3.5,unit:"hectare"}`, requested_alternatives and explicit
`parameters:{ns_green_seconds:55}`. Without parameters, deterministic rules generate
25%, 50%, 100% movement toward demand-proportional allocation. A positive affected
area allowance is satisfied because this demo timing operation takes no land.
No LLM is used. Responses include expected_impacts with qualitative directions,
validation, generated_at, assumptions and rejected_alternatives.

Evaluate requires analysis_id, baseline_id, proposal_set_id, alternative_level,
and the selected alternative's **complete unchanged interventions array**.
Optional area must match the saved analysis. Optional evaluation.indicators selects
from `ns_delay`, `ew_delay`, `mean_delay`; omitted/empty selects all. Unknown metrics
return 422. The scenario retains demand, cycle and lost time. Delta is scenario minus
baseline, so negative delay is better. Baseline evidence is copied from analysis.
Responses include structured uncertainty/provenance, timestamps and simulation
metadata. No traffic simulation ran: `status:"not_requested", mode:"none"`.

An explicit evaluation request such as
`"evaluation":{"traffic_simulation":{"requested":true,"mode":"live"}}`
returns `503 sumo_unavailable`. Offline/replay are also unavailable; replay requests
must supply replay_id. No fallback or fabricated run metadata is returned.

Errors: `{"error":{"code":"...","message":"...","details":[],"request_id":"req_..."}}`.
400 malformed JSON; 422 schema/geometry/unsupported metric; 404 unknown area,
analysis, issue, proposal or evaluation; 409 incompatible baseline/area/selection;
503 unavailable SUMO, storage or capacity. Records survive restarts in SQLite.

[Complete captured requests and responses](demo-flow.json) use the actual API.
Generate a live flow with:

```sh
python3 -m uv run --locked python -m backend.demo_client
```

The aspirational geographic API and API_ENDPOINTS examples are not implemented
capabilities. No observed sensor traffic, underpass, turbo roundabout or AI provider
from those examples is advertised by this implementation.
