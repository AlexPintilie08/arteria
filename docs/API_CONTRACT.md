# Proposed API contract

This document defines a draft JSON contract for the backend. It is not an implemented API. All coordinates use GeoJSON ordering `[longitude, latitude]`; spatial calculations must also identify the working CRS. Timestamps use ISO 8601 UTC. Each numeric measurement includes a unit and provenance. `observed`, `calculated`, `estimated`, and `unknown` describe epistemic status and must not be collapsed into one another.

## Implemented bootstrap endpoint: `GET /health`

The local foundation implements a liveness endpoint only. It requires no AI key or external data service.

### Response

```json
{"status": "ok", "service": "arteria-backend"}
```

The planned `/analyze`, `/propose`, and `/evaluate` endpoints below are not implemented yet.

## Shared conventions

### Geographic identifier

```json
{
  "city_id": "iasi-ro",
  "area_id": "iasi-example-neighborhood",
  "boundary": {
    "type": "Polygon",
    "coordinates": [[[27.58, 47.16], [27.59, 47.16], [27.59, 47.17], [27.58, 47.16]]]
  },
  "boundary_source": "user_selected",
  "crs": "EPSG:4326"
}
```

`area_id` may identify a known administrative/neighborhood area or a user-drawn area. When both a known identifier and boundary are provided, the backend verifies that they are consistent. Enforce configured area and geometry limits.

### Provenance and uncertainty

```json
{
  "status": "calculated",
  "provenance": [{
    "source": "OpenStreetMap",
    "source_version": "2026-10-01",
    "retrieved_at": "2026-10-02T10:00:00Z",
    "method": "network_reachable_population_within_threshold",
    "crs": "EPSG:3844"
  }],
  "uncertainty": {
    "kind": "coverage_limitation",
    "description": "Transit stop coverage may be incomplete.",
    "interval": null,
    "confidence": null
  }
}
```

For values with quantifiable uncertainty, provide a documented interval or method-specific confidence. Do not invent numeric confidence. An unknown value has `value: null`, `status: "unknown"`, and a reason.

### Error response

```json
{
  "error": {
    "code": "unsupported_intervention",
    "message": "The requested intervention type is not supported.",
    "details": [{"field": "intervention.type", "reason": "Not in the supported catalog."}],
    "request_id": "req_01J..."
  }
}
```

Use standard HTTP status codes: 400 for malformed JSON, 422 for schema or constraint validation, 404 for unknown resources, 409 for incompatible scenario state, 429 for rate limits, and 500/503 for internal or upstream unavailability. Do not return secrets, raw provider credentials, or unfiltered provider errors.

## `POST /analyze`

Analyzes supported geographic features and returns detected issue candidates and indicators. Inputs should allow callers to request available layers and methods without implying that every layer exists.

### Request

```json
{
  "area": {
    "city_id": "iasi-ro",
    "area_id": "iasi-example-neighborhood",
    "boundary": null,
    "boundary_source": "known_area",
    "crs": "EPSG:4326"
  },
  "layers": ["roads", "walking", "cycling", "public_transport", "parking", "green_space", "buildings", "points_of_interest"],
  "analysis": {
    "network_modes": ["walk", "bike"],
    "accessibility_thresholds": [{"value": 15, "unit": "minute", "mode": "walk"}]
  },
  "data_as_of": null
}
```

### Response

```json
{
  "analysis_id": "an_01J...",
  "area": {"city_id": "iasi-ro", "area_id": "iasi-example-neighborhood", "crs": "EPSG:4326"},
  "created_at": "2026-10-02T10:02:00Z",
  "indicators": [{
    "id": "walk_access_example",
    "label": "Residents within selected walking threshold of a service",
    "value": null,
    "unit": "person",
    "status": "unknown",
    "provenance": [],
    "uncertainty": {"kind": "missing_data", "description": "Population and service coverage not available.", "interval": null, "confidence": null}
  }],
  "issues": [],
  "layer_availability": [{"layer": "cycling", "status": "unknown", "reason": "Coverage has not been established."}],
  "warnings": []
}
```

An issue is an evidence-backed candidate, not an AI finding. Each issue should reference supporting indicators and geometry, and carry status, provenance, and uncertainty.

## `POST /propose`

Requests structured alternatives for an issue. The backend supplies spatial evidence to the cloud model and validates results against supported intervention types and geographic constraints.

### Request

```json
{
  "analysis_id": "an_01J...",
  "area": {"city_id": "iasi-ro", "area_id": "iasi-example-neighborhood"},
  "issue_id": "issue_01J...",
  "intervention_catalog_version": "catalog-1",
  "constraints": {"max_affected_area": {"value": 2, "unit": "hectare"}},
  "requested_alternatives": ["minimal", "moderate", "transformative"]
}
```

### Response

```json
{
  "proposal_set_id": "ps_01J...",
  "analysis_id": "an_01J...",
  "model": {"provider": "cloud", "model_id": "provider-model", "generated_at": "2026-10-02T10:05:00Z"},
  "alternatives": [{
    "level": "minimal",
    "summary": "Review crossings on the selected corridor and improve one supported crossing location.",
    "interventions": [{
      "type": "crossing_upgrade",
      "geometry": {"type": "Point", "coordinates": [27.58, 47.16]},
      "parameters": {"treatment": "raised"},
      "parameter_units": {},
      "affected_feature_ids": ["osm-way-or-node-id"]
    }],
    "rationale": "Addresses the selected evidence-backed crossing issue.",
    "expected_impacts": [{"indicator_id": "pedestrian_connectivity", "direction": "increase", "value": null, "unit": null, "status": "estimated", "provenance": [], "uncertainty": {"kind": "qualitative_estimate", "description": "Requires evaluation to quantify.", "interval": null, "confidence": null}}],
    "assumptions": ["The selected crossing is within the supported road network."],
    "validation": {"status": "accepted", "checks": ["supported_type", "inside_area", "parameters_valid"]}
  }],
  "rejected_alternatives": [],
  "warnings": ["Expected impacts are hypotheses; no simulation was run."]
}
```

Supported intervention types and parameter schemas are versioned server-side. A response must not be accepted merely because it is valid JSON. Reject or explicitly mark alternatives that fail geometry, type, parameter, conflict, or evidence checks. Proposal impact statements may be qualitative estimates; they are never simulation results.

## `POST /evaluate`

Creates a virtual scenario and recomputes eligible indicators. A SUMO run is optional and must report whether it actually ran or whether the response is a stored replay.

### Request

```json
{
  "analysis_id": "an_01J...",
  "area": {"city_id": "iasi-ro", "area_id": "iasi-example-neighborhood"},
  "baseline_id": "baseline_01J...",
  "proposal_set_id": "ps_01J...",
  "alternative_level": "minimal",
  "interventions": [{"type": "crossing_upgrade", "geometry": {"type": "Point", "coordinates": [27.58, 47.16]}, "parameters": {"treatment": "raised"}}],
  "evaluation": {
    "indicators": ["pedestrian_connectivity"],
    "traffic_simulation": {"requested": false, "mode": "none", "replay_id": null}
  }
}
```

`traffic_simulation.mode` may be `none`, `live`, `offline`, or `replay`. Require a replay identifier for `replay`; live/offline must create a real simulator run. Do not silently fall back from a requested run to replay.

### Response

```json
{
  "evaluation_id": "ev_01J...",
  "scenario_id": "sc_01J...",
  "created_at": "2026-10-02T10:10:00Z",
  "baseline": {"id": "baseline_01J...", "source_snapshot": "osm-2026-10-01"},
  "scenario": {"id": "sc_01J...", "intervention_catalog_version": "catalog-1"},
  "comparisons": [{
    "indicator_id": "pedestrian_connectivity",
    "baseline": {"value": null, "unit": "ratio", "status": "unknown", "provenance": [], "uncertainty": {"kind": "missing_data", "description": "Baseline inputs unavailable.", "interval": null, "confidence": null}},
    "scenario": {"value": null, "unit": "ratio", "status": "unknown", "provenance": [], "uncertainty": {"kind": "missing_data", "description": "Scenario inputs unavailable.", "interval": null, "confidence": null}},
    "delta": {"value": null, "unit": "ratio", "status": "unknown", "provenance": [], "uncertainty": {"kind": "not_computable", "description": "Both values are required.", "interval": null, "confidence": null}}
  }],
  "simulation": {"status": "not_requested", "mode": "none", "run_id": null, "started_at": null, "completed_at": null, "simulator": null, "configuration": null, "measurements": []},
  "warnings": []
}
```

For a real run, return simulator and version, mode, configuration, timestamps, input/demand provenance, and measured outputs with units and uncertainty. For a replay, set `mode: "replay"` and include the original run ID and timestamp. If SUMO is unavailable or a run fails, report a specific status and error; never substitute LLM-generated measurements.
