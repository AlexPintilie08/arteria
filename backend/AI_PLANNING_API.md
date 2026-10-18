# SIM grounded AI planning API

This API adds evidence interpretation to an immutable SIM spatial study. SIM
detects the mapped problems, creates the solution plan, and owns candidate
geometry and numerical impacts. The cloud model can explain only IDs and
evidence already present in the stored packet. SIM validates the model response
before the backend persists or returns it.

The provider is optional and disabled by default. A missing provider produces an
explicit `provider_unavailable` planning result; it does not return deterministic
text as if it came from a model. A successful request does not run SUMO or prove
physical, legal, or construction feasibility.

## Environment

Copy `.env.example` to an untracked `.env` and set these backend-only values when
cloud planning is intentionally enabled:

```dotenv
ARTERIA_AI_ENABLED=true
ARTERIA_AI_PROVIDER=openai
ARTERIA_AI_MODEL=gpt-4o-mini
ARTERIA_AI_API_KEY=your-server-side-key
ARTERIA_AI_BASE_URL=https://api.openai.com/v1
ARTERIA_AI_TIMEOUT_SECONDS=18
```

`OPENAI_API_KEY` is also accepted as a server environment fallback. The provider
uses the OpenAI Responses API with strict JSON Schema output. The base URL must
use HTTPS. Requests are bounded by the configured timeout (maximum 20 seconds)
and provider response envelope size; response storage contains no credentials.

## User flow

1. Select an actual catalog area ID from the SIM neighborhood catalog.
2. Create a spatial study with `source: "osm"` and that `neighborhood_id`.
3. Display the study's `urban_issues`, `problem_locations_geojson`, and
   `solution_plan`. A problem may have no geometry; do not invent a marker.
4. Call the planning endpoint using the same stored study. It does not reacquire
   OSM or regenerate the evidence packet.
5. Render only `identified_problems` and `recommended_solutions` returned by
   SIM validation. Use each recommendation's `authoritative_sim_solution` for
   candidate geometry, intervention, validation, and impacts.
6. Retrieve a saved result with its `planning_id`; retrieval never calls a model.

### Create a study

`POST /api/v1/spatial/studies`

```json
{
  "source": "osm",
  "neighborhood_id": "osm-w-670153116",
  "sample_count": 16,
  "max_candidates": 3,
  "seed": "arteria-spatial-v1"
}
```

The API validates the area against SIM's catalog and analysis limits. A point-only
place or an area requiring controlled analysis is rejected. Failed OSM requests
never fall back to a fixture. The response retains the existing study fields and
adds:

- `urban_issues`: detected problems, coverage gaps, evidence, and uncertainty.
- `solution_plan`: evidence-linked SIM candidates and non-executable concepts.
- `ai_evidence_packet`: the bounded immutable packet used for later model calls.
- `problem_locations_geojson`: SIM's problem geometries, WGS84 longitude/latitude.
- `evidence_packet_sha256`: the packet's SIM-generated integrity hash.

OSM study creation can take up to the existing 90-second worker deadline. It
queries pedestrian graph data and bounded feature categories (schools,
healthcare, public transport, and crossings); other unqueried data remains
unknown. OSM features and place extents are not certified municipal boundaries.

The existing candidate and evaluation routes stay unchanged:

- `GET /api/v1/spatial/studies/{study_id}`
- `GET /api/v1/spatial/studies/{study_id}/candidates`
- `POST /api/v1/spatial/studies/{study_id}/evaluate`

### Request AI planning

`POST /api/v1/spatial/studies/{study_id}/planning`

The request body is optional; `{}` is accepted. The endpoint intentionally does
not accept a client-authored prompt, evidence, coordinates, or candidate IDs.
The packet and model prompt come from the stored study and SIM.

```http
POST /api/v1/spatial/studies/study_123/planning
Content-Type: application/json
Idempotency-Key: 6e4b7ae4-92ca-4a3e-b35d-9d72a3acb217
```

The idempotency header is optional. If provided, it is scoped to the study and
stored as a hash. Repeating a completed request with the same key returns the
same result without a second provider call. A concurrent duplicate receives
`409` while the first request is running. Use a new key for an intentional retry.
Without the header, each POST is a new planning attempt.

Every completed HTTP request returns `200` with one immutable planning result,
including explicit provider failure statuses. A valid provider response resembles:

```json
{
  "planning_id": "planning_123",
  "study_id": "study_123",
  "baseline_id": "graph_123",
  "source": "osm",
  "area_id": "osm-w-670153116",
  "engine_revision": "<SIM snapshot revision>",
  "calculation": "pedestrian_graph",
  "evidence_packet_sha256": "<64-character SIM packet hash>",
  "provider_status": "completed",
  "provider": "openai",
  "model_id": "gpt-4o-mini",
  "ai_generated": true,
  "summary": "Dovezile cartografiate justifică o verificare suplimentară în teren.",
  "identified_problems": [
    {
      "problem_id": "prob_<SIM id>",
      "explanation": "Graful sugerează o posibilă discontinuitate care necesită verificare pe teren.",
      "evidence_ids": ["ev_<SIM id>"]
    }
  ],
  "recommended_solutions": [
    {
      "solution_id": "sol_<SIM id>",
      "candidate_id": "cand_<SIM id>",
      "problem_ids": ["prob_<SIM id>"],
      "title": "Verificarea opțiunii documentate de SIM",
      "explanation": "Opțiunea se bazează pe dovezile citate; verificarea fizică rămâne necesară.",
      "expected_benefit_type": "<SIM value>",
      "evidence_ids": ["ev_<SIM id>"],
      "field_verification_required": true,
      "authoritative_sim_solution": {
        "solution_id": "sol_<SIM id>",
        "candidate_id": "cand_<SIM id>",
        "geometry": "<copied from the validated SIM candidate, when present>",
        "intervention": "<exact SIM intervention, when present>",
        "shared_sample_impact": "<SIM-calculated impact, when present>"
      }
    }
  ],
  "validation": {
    "schema_version": "arteria.ai-planning-validation.v1",
    "status": "validated",
    "findings": [],
    "rejected_entry_count": 0
  },
  "error_code": null,
  "created_at": "2026-10-18T12:00:00Z",
  "warnings": [
    "AI planning interprets stored SIM evidence; it does not execute SUMO or determine physical feasibility."
  ]
}
```

The example IDs and impact values are placeholders. The API copies actual IDs,
geometry, interventions, and impacts from the stored packet after SIM validation.
The model cannot add authoritative geometry, metrics, costs, citations, or
feasibility claims.

### Provider availability statuses

| `provider_status` | Meaning | `ai_generated` |
| --- | --- | --- |
| `provider_unavailable` | Disabled, unsupported provider, missing key, or invalid configuration; no cloud response | `false` |
| `timeout` | Provider request exceeded the bounded deadline | `false` |
| `provider_error` | Network, HTTP, or provider-envelope failure | `false` |
| `invalid_response` | Cloud response arrived but SIM rejected its JSON/schema/packet binding | `true` |
| `completed_with_rejections` | SIM retained valid entries and reported rejected entries in `validation.findings` | `true` |
| `completed` | SIM accepted the full model response | `true` |

For `provider_unavailable`, `timeout`, or `provider_error`, the recommendation
arrays are empty and `provider`/`model_id` are null. Error codes are sanitized;
provider response bodies, prompts, and API keys are not returned. A timeout or
provider failure leaves the original spatial study intact.

### Retrieve a saved planning result

`GET /api/v1/spatial/studies/{study_id}/planning/{planning_id}` returns the exact
stored result. It returns `404` if the result does not belong to that study.

### Error envelope

Route errors use the existing backend format:

```json
{
  "error": {
    "code": "unknown_resource",
    "message": "Unknown spatial study",
    "details": [],
    "request_id": "req_<generated id>"
  }
}
```

- `404`: unknown study or planning result.
- `409`: study has no valid packet, packet integrity mismatch, or duplicate
  idempotency key is still running.
- `422`: malformed body, unsupported request fields, or invalid idempotency key.
- `503`: storage unavailable or capacity reached.

## Frontend fetch example

```ts
type PlanningResult = {
  planning_id: string;
  study_id: string;
  baseline_id: string;
  area_id: string;
  evidence_packet_sha256: string;
  provider_status:
    | "provider_unavailable"
    | "timeout"
    | "provider_error"
    | "invalid_response"
    | "completed_with_rejections"
    | "completed";
  ai_generated: boolean;
  summary: string | null;
  identified_problems: Array<Record<string, unknown>>;
  recommended_solutions: Array<Record<string, unknown>>;
  validation: Record<string, unknown> | null;
  warnings: string[];
};

async function requestPlanning(apiBase: string, studyId: string): Promise<PlanningResult> {
  const response = await fetch(
    `${apiBase}/api/v1/spatial/studies/${encodeURIComponent(studyId)}/planning`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: "{}",
    },
  );
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.error?.message ?? `Planning failed (${response.status})`);
  }
  return payload as PlanningResult;
}
```

Keep the generated idempotency key if retrying the same user action. Treat
`provider_unavailable`, `timeout`, and `provider_error` as unavailable states;
never fill the UI with demo suggestions. For `completed_with_rejections`, show
only validated entries and optionally summarize `validation.findings`. Render
`problem_locations_geojson` as WGS84 GeoJSON and use the attached authoritative
SIM candidate records for candidate details. Show `warnings` and keep feasibility
unknown unless another verified source establishes it.

## Persistence and deployment boundary

Studies and planning results use the existing immutable SQLite JSON store and
survive backend process restarts. Idempotency records are capped with planning
results. SQLite is local single-machine persistence; this API has no user
authentication or per-user isolation and is intended for the controlled demo.
