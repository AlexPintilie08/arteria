# Backend

## Responsibilities

Provide the HTTP/JSON API; validate requests and responses; orchestrate urban analysis; prepare bounded spatial context for a cloud LLM; return structured intervention recommendations; coordinate scenario evaluation; and communicate with the independent spatial/simulation component. A local Qwen model is an optional fallback, not the primary path.

## Planned technology

Python, FastAPI, Pydantic, and a cloud LLM API. Provider-specific code should sit behind a narrow interface so recommendation validation and API contracts do not depend on one model vendor.

## Inputs and outputs

- **Inputs:** geographic identifiers, analysis options, user-selected problems, supported intervention definitions, baseline/scenario identifiers, and available data metadata.
- **Outputs:** validated analysis findings, provenance and uncertainty, constrained proposal alternatives, and evaluation results returned by the spatial/simulation layer.

## Integration interfaces

Expose the proposed `POST /analyze`, `POST /propose`, and `POST /evaluate` interfaces described in `docs/API_CONTRACT.md`. The backend calls `sim` through an internal Python interface or a separately defined service boundary; this choice should follow the first deployment and runtime needs.

## Implementation objectives

Validate all external input, keep provider secrets server-side, constrain LLM context to relevant spatial evidence, validate generated proposals against an explicit intervention catalog and geographic constraints, and report unavailable or uncertain evidence. Evaluation results must originate from deterministic analysis or a real simulation run/replay record, never from LLM prose.

## Technical risks

LLM outputs may be invalid, unsupported, or overconfident; treat them as untrusted structured suggestions. Spatial context can be large and sensitive to data quality. Provider latency, rate limits, and outages need bounded timeouts and clear errors. Units, coordinate reference systems, provenance, and uncertainty must survive every boundary.
