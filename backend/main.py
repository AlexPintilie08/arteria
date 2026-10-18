"""Frontend-ready, explicitly synthetic ARTERIA demonstration API."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.models import (
    Alternative, AnalysisResponse, AnalyzeRequest, Comparison, EvaluationResponse,
    EvaluateRequest, Indicator, Inputs, Intervention, Measurement, Parameters,
    ProposalResponse, ProposeRequest, Reference, Issue, Point, LayerAvailability,
    Uncertainty, ExpectedImpact, ErrorResponse, AreasResponse, AreaBookmark,
)
from backend.settings import settings
from backend.storage import Store, CapacityError, StorageUnavailable
from backend.catalog import bookmark, BOOKMARKS
from backend.simulation_adapter import SimulationAdapter, SimulationUnavailable

app = FastAPI(title="ARTERIA API", version="0.3.0", description="Explicit synthetic DEMO; no city measurements or SUMO scenario integration.",
    responses={status: {"model": ErrorResponse} for status in (400, 404, 409, 422, 502, 503, 504)})
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"],
                   allow_headers=["Content-Type"])
adapter = SimulationAdapter()
analyses = Store("analyses-v3", AnalysisResponse)
proposals = Store("proposals-v3", ProposalResponse)
evaluations = Store("evaluations-v3", EvaluationResponse)
MAX_RECORDS = 1000


def identity(prefix, value):
    return prefix + sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:24]


def error(status, code, message, details=None):
    return JSONResponse(status_code=status, content={"error": {
        "code": code, "message": message, "details": details or [], "request_id": "req_" + uuid4().hex}})


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    return error(exc.status_code, {404: "unknown_resource", 409: "incompatible_scenario", 503: "capacity_unavailable"}.get(exc.status_code, "invalid_request"), str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    malformed = any(e["type"] == "json_invalid" for e in exc.errors())
    return error(400 if malformed else 422, "validation_error", "Request validation failed", [
        {"field": ".".join(map(str, e["loc"])), "reason": e["msg"]} for e in exc.errors()])


@app.exception_handler(SimulationUnavailable)
async def unavailable(request: Request, exc: SimulationUnavailable):
    return error(503, "sumo_unavailable", str(exc))


@app.exception_handler(StorageUnavailable)
async def storage_error(request: Request, exc: StorageUnavailable):
    return error(503, "storage_unavailable", "Database temporarily unavailable; check server storage configuration.")


@app.exception_handler(CapacityError)
async def capacity_error(request: Request, exc: CapacityError):
    return error(503, "capacity_unavailable", str(exc))


def lookup(store, key):
    result = store.get(key)
    if result is None:
        raise HTTPException(404, "Unknown identifier: " + key)
    return result


def save(store, key, value):
    return store.put(key, value, MAX_RECORDS)


def check_area(area, analysis):
    if area is not None and (area.city_id, area.area_id) != (analysis.area.city_id, analysis.area.area_id):
        raise HTTPException(409, "Area does not match analysis")


def demo_point(area):
    selected = bookmark(area.area_id)
    if selected is None:
        raise HTTPException(404, "Unknown area. Use GET /api/v1/areas for supported demo contexts.")
    point = Point(coordinates=selected[1])
    if area.boundary is not None:
        from shapely.geometry import shape
        if not shape(area.boundary.model_dump()).covers(shape(point.model_dump())):
            raise HTTPException(422, "Selected boundary does not contain the demo bookmark")
    return point


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "arteria-backend"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(body: AnalyzeRequest):
    if body.mode == "sumo":
        adapter.require_sumo()
    point = demo_point(body.area)
    if body.data_as_of is not None:
        raise HTTPException(422, "Historical data is unavailable in DEMO mode; use data_as_of: null")
    key = {"request": body.model_dump(mode="json"), "engine": adapter.version}
    aid, bid = identity("an_", key), identity("baseline_", key)
    result = AnalysisResponse(analysis_id=aid, baseline_id=bid, area=body.area,
        created_at=datetime.now(timezone.utc), inputs=body.inputs,
        issues=[Issue(geometry=point)],
        layer_availability=[LayerAvailability(layer=layer) for layer in dict.fromkeys(body.layers)],
        warnings=["DEMO: synthetic intersection inputs, not local traffic observations or a SUMO run.",
                  "Area names and supplied boundaries are display context only; no boundary certification or geographic analysis is performed.",
                  "Network modes and accessibility thresholds cannot be calculated without geographic data; requested layers are unknown."],
        indicators=[Indicator(id=k, label=k.replace("_", " "), value=v)
                    for k, v in adapter.indicators(body.inputs).items()])
    return save(analyses, aid, result)


@app.post("/propose", response_model=ProposalResponse)
def propose(body: ProposeRequest):
    analysis = lookup(analyses, body.analysis_id)
    check_area(body.area, analysis)
    if body.issue_id not in {issue.id for issue in analysis.issues}:
        raise HTTPException(404, "Unknown issue for this analysis")
    inputs = analysis.inputs
    if body.parameters is not None:
        try:
            Inputs.model_validate({**inputs.model_dump(), **body.parameters.model_dump()})
        except ValueError as exc:
            raise HTTPException(422, "Selected green time leaves less than 10 seconds for the opposing phase") from exc
    available = inputs.cycle_seconds - inputs.lost_seconds
    target = max(10, min(available - 10, available * inputs.ns_demand_vph /
                        (inputs.ns_demand_vph + inputs.ew_demand_vph)))
    alternatives = []
    for level in dict.fromkeys(body.requested_alternatives):
        fraction = {"minimal": .25, "moderate": .5, "transformative": 1.0}[level]
        green = (body.parameters.ns_green_seconds if body.parameters is not None else
                 inputs.ns_green_seconds + fraction * (target - inputs.ns_green_seconds))
        candidate_inputs = Inputs.model_validate({**inputs.model_dump(), "ns_green_seconds": green})
        before, after = adapter.indicators(inputs), adapter.indicators(candidate_inputs)
        impacts = [ExpectedImpact(indicator_id=k, value=None,
            direction="decrease" if after[k] < v else "increase" if after[k] > v else "unchanged",
            uncertainty=Uncertainty(kind="qualitative_estimate", description="Direction from the synthetic demo model; run evaluate for numeric comparison."))
            for k, v in before.items()]
        alternatives.append(Alternative(level=level,
            summary=f"Set north–south green to {green:.2f} seconds.",
            interventions=[Intervention(parameters=Parameters(ns_green_seconds=green), geometry=analysis.issues[0].geometry)],
            expected_impacts=impacts,
            rationale=("Evaluate the user-selected green time with fixed demand and cycle; opposing traffic may worsen." if body.parameters else "Move toward demand-proportional green allocation; opposing traffic may experience more delay. Transformative denotes the full timing adjustment, not infrastructure works.")))
    result = ProposalResponse(proposal_set_id=identity("ps_", body.model_dump()),
        analysis_id=analysis.analysis_id, baseline_id=analysis.baseline_id, alternatives=alternatives)
    return save(proposals, result.proposal_set_id, result)


@app.post("/evaluate", response_model=EvaluationResponse)
def evaluate(body: EvaluateRequest):
    analysis = lookup(analyses, body.analysis_id)
    proposal = lookup(proposals, body.proposal_set_id)
    check_area(body.area, analysis)
    if body.baseline_id != analysis.baseline_id or proposal.analysis_id != analysis.analysis_id:
        raise HTTPException(409, "Baseline, analysis and proposal must belong to the same scenario")
    selected = next((a for a in proposal.alternatives if a.level == body.alternative_level), None)
    if selected is None or body.interventions != selected.interventions:
        raise HTTPException(409, "Interventions must match the selected server-issued alternative")
    if body.evaluation.traffic_simulation.requested:
        adapter.require_sumo()
    scenario_inputs = Inputs.model_validate({**analysis.inputs.model_dump(),
        "ns_green_seconds": body.interventions[0].parameters.ns_green_seconds})
    before, after = adapter.indicators(analysis.inputs), adapter.indicators(scenario_inputs)
    names = list(dict.fromkeys(body.evaluation.indicators)) or list(before)
    unsupported = set(names) - set(before)
    if unsupported:
        raise HTTPException(422, "Unsupported demo indicators: " + ", ".join(sorted(unsupported)))
    comparisons = []
    for name in names:
        value = before[name]
        delta = after[name] - value
        baseline_measure = next(item for item in analysis.indicators if item.id == name)
        comparisons.append(Comparison(indicator_id=name, baseline=Measurement.model_validate(baseline_measure.model_dump(exclude={"id", "label"})),
            scenario=Measurement(value=after[name]), delta=Measurement(value=delta),
            percent_change=100 * delta / value,
            impact="improved" if delta < -1e-9 else "worsened" if delta > 1e-9 else "unchanged"))
    sid = identity("sc_", body.model_dump())
    result = EvaluationResponse(evaluation_id=identity("ev_", body.model_dump()), scenario_id=sid,
        created_at=datetime.now(timezone.utc), baseline=Reference(id=analysis.baseline_id),
        scenario=Reference(id=sid), baseline_inputs=analysis.inputs, scenario_inputs=scenario_inputs,
        comparisons=comparisons)
    return save(evaluations, result.evaluation_id, result)


@app.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str):
    return lookup(analyses, analysis_id)


@app.get("/proposals/{proposal_set_id}", response_model=ProposalResponse)
def get_proposal(proposal_set_id: str):
    return lookup(proposals, proposal_set_id)


@app.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(evaluation_id: str):
    return lookup(evaluations, evaluation_id)


@app.get("/api/v1/areas", response_model=AreasResponse)
def list_areas(city_id: str = "iasi-ro", include_bounds: bool = True):
    if city_id != "iasi-ro":
        raise HTTPException(404, "Unsupported city")
    return AreasResponse(areas=[AreaBookmark(id=key, slug=key, name=name, center=center)
                                for key, (name, center) in BOOKMARKS.items()])


# Optional graph engine is isolated from the traffic-demo models and lifecycle.
from backend.spatial_adapter import (
    SpatialAreaRejected, SpatialNeighborhoodNotFound, SpatialUnavailable, SpatialTimeout, SpatialFailure,
)
from backend.spatial_routes import router as spatial_router


@app.exception_handler(SpatialUnavailable)
async def spatial_unavailable(request: Request, exc: SpatialUnavailable):
    return error(503, "spatial_unavailable", str(exc))


@app.exception_handler(SpatialTimeout)
async def spatial_timeout(request: Request, exc: SpatialTimeout):
    return error(504, "spatial_timeout", str(exc))


@app.exception_handler(SpatialFailure)
async def spatial_failure(request: Request, exc: SpatialFailure):
    return error(502, "spatial_failure", str(exc))


@app.exception_handler(SpatialAreaRejected)
async def spatial_area_rejected(request: Request, exc: SpatialAreaRejected):
    return error(422, "study_area_rejected", str(exc))


@app.exception_handler(SpatialNeighborhoodNotFound)
async def spatial_neighborhood_not_found(request: Request, exc: SpatialNeighborhoodNotFound):
    return error(404, "unknown_neighborhood", str(exc))


app.include_router(spatial_router)
