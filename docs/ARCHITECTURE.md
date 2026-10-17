# ARTERIA architecture

## Component boundaries

The application has exactly three main components:

- **`frontend/`** owns map interaction, geographic selection, layers, indicators, proposal presentation, scenario controls, comparisons, and simulation visualization/replay. It does not calculate authoritative analysis or call an LLM directly.
- **`backend/`** owns the public HTTP/JSON API, validation, orchestration, spatial context preparation, cloud LLM access, recommendation constraints, and evaluation coordination. Provider credentials remain server-side.
- **`sim/`** owns geographic data preparation, spatial networks and calculations, issue detection, virtual network changes, and optional SUMO traffic runs. Core network analysis remains usable without SUMO.

The initial integration can call `sim` in-process from the backend. Keep the boundary explicit so it can become a service if deployment or scaling needs demand it. The frontend communicates only with the backend contract.

## Data pipeline

1. Select a supported geographic area and record its identifier, boundary source, and coordinate reference system.
2. Acquire source datasets such as OpenStreetMap extracts and any separately licensed public datasets. Record source, retrieval time, version, coverage, and license.
3. Normalize geometries and networks in `sim`, retaining source identifiers and reporting invalid or missing coverage.
4. Calculate supported indicators and issue candidates. Return observed values separately from derived values, estimates, and unavailable information.
5. Prepare the smallest relevant spatial evidence set for the backend and, if needed, the cloud LLM.
6. Create an immutable baseline reference and a separate scenario copy for each virtual intervention.
7. Recalculate geographic indicators; run SUMO only if the requested question, network, and demand inputs support it.
8. Return baseline and scenario results with methods, units, provenance, assumptions, and uncertainty.

## Geographic analysis

OSMnx and related geospatial tools can build walk, cycle, or drive networks and support connectivity and accessibility measures. GeoPandas and Shapely can manage and validate geometries; NetworkX can support graph calculations. Building, transit, parking, green-space, and point-of-interest coverage depends on available and current data. An absent feature is unknown unless the source can establish that it is truly absent.

Every measure must state its unit and method. Distinguish source observations from calculations based on those observations. Do not compare values with incompatible boundaries, timestamps, network modes, or assumptions without disclosing the difference.

## AI recommendation workflow

1. The user chooses an issue and requests proposals for a geographic area.
2. The backend retrieves validated analysis evidence and a versioned catalog of supported intervention types.
3. The backend sends the cloud model only relevant evidence, constraints, and the required structured response schema. Local Qwen can be an optional fallback.
4. The model returns minimal, moderate, and transformative alternatives with rationale, affected features, prerequisites, and expected direction of impact. These are hypotheses, not results.
5. Pydantic validates response shape; backend rules validate intervention type, geometry and area constraints, conflicts, and required evidence. Unsupported proposals are rejected or returned as unavailable for review.
6. The user selects an accepted proposal. The backend creates a scenario and asks `sim` to apply supported changes and recompute applicable indicators.

The LLM does not produce or fill in simulation measurements. If an impact cannot be computed, show it as unknown or a clearly labeled estimate with method and uncertainty.

## Intervention validation

Maintain an explicit catalog with allowed parameters, units, geometry requirements, geographic constraints, and computable effects. Validate geometry against the selected area, supported network features, parameter ranges, and conflicts with existing or proposed interventions. Reject malformed, out-of-area, unsupported, or unverifiable changes. Store accepted scenario changes separately from baseline source data and retain a trace to the proposal and validation result.

## SUMO architecture

SUMO is an optional CPU-based microscopic vehicle simulator for scenarios with appropriate road networks and traffic demand. Geographic analysis and indicators that do not require vehicle dynamics must run without it. A live run is bounded and returns actual execution metadata. An offline run records immutable inputs, SUMO version, configuration, seed, and outputs for reproducibility. A replay visualizes a stored run and is explicitly labeled with its run ID and time; it never implies a fresh run.

Do not present uncalibrated demand or simulation as a prediction of real-world outcomes. Report the scenario assumptions and limitations alongside each result.

## Before/After evaluation

Use the same area, source snapshot, method, and parameters for baseline and intervention calculations when possible. Return both values, units, deltas, provenance, and uncertainty. If a scenario changes network topology, record that change and the resulting network version. Keep calculated accessibility/connectivity metrics distinct from traffic simulation metrics. Mark unavailable comparisons as unknown rather than manufacturing a value.

## Assumptions and data limitations

- Iași is the first city, but geographic identifiers and component interfaces should support other neighborhoods and later cities.
- OpenStreetMap and other data may be incomplete, stale, unevenly tagged, or subject to licensing limits.
- Coverage differs between modes and neighborhoods; no data does not mean no issue.
- Network measures depend on boundary, routing mode, graph preparation, thresholds, and source date.
- Traffic simulation requires demand assumptions and calibration. Its results describe the modeled scenario, not guaranteed real-world effects.
- Cloud model availability, latency, and output quality vary. Recommendations remain constrained hypotheses.
- All units, provenance, assumptions, and uncertainty should travel with values through the API and user interface.
