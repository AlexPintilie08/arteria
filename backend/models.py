"""Public demo contract. Unsupported fields are rejected instead of ignored."""
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class AreaRef(Model):
    city_id: Literal["iasi-ro"] = "iasi-ro"
    area_id: str = Field(min_length=1, max_length=100)


class Polygon(Model):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[tuple[float, float]]] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def valid_polygon(self):
        from shapely.geometry import shape
        from pyproj import Geod
        if sum(map(len, self.coordinates)) > 2000:
            raise ValueError("Polygon has too many vertices (maximum 2000)")
        for ring in self.coordinates:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError("Polygon rings must be closed with at least four positions")
            if any(not (27.3 <= lon <= 27.9 and 46.9 <= lat <= 47.4) for lon, lat in ring):
                raise ValueError("Boundary must lie within the supported Iași study envelope")
        polygon = shape(self.model_dump())
        if polygon.is_empty or not polygon.is_valid:
            raise ValueError("Invalid polygon geometry")
        area, _ = Geod(ellps="WGS84").geometry_area_perimeter(polygon)
        if abs(area) > 5_000_000 or abs(area) < 1:
            raise ValueError("Study boundary must cover between 1 m² and 5 km²")
        return self


class Point(Model):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]


class Area(AreaRef):
    boundary: Polygon | None = None
    boundary_source: Literal["known_area", "user_selected"] = "known_area"
    crs: Literal["EPSG:4326"] = "EPSG:4326"

    @model_validator(mode="after")
    def user_boundary(self):
        if self.boundary_source == "user_selected" and self.boundary is None:
            raise ValueError("A user-selected area requires a boundary")
        return self


Layer = Literal["roads", "walking", "cycling", "public_transport", "parking", "green_space", "buildings", "points_of_interest"]


class Threshold(Model):
    value: float = Field(gt=0, le=120)
    unit: Literal["minute"] = "minute"
    mode: Literal["walk", "bike", "drive"]


class AnalysisOptions(Model):
    network_modes: list[Literal["walk", "bike", "drive"]] = Field(default_factory=lambda: ["drive"], min_length=1, max_length=3)
    accessibility_thresholds: list[Threshold] = Field(default_factory=list, max_length=12)


class Inputs(Model):
    cycle_seconds: float = Field(default=90, ge=60, le=180)
    ns_green_seconds: float = Field(default=40, ge=10)
    lost_seconds: Literal[10] = 10
    ns_demand_vph: float = Field(default=700, ge=100, le=1500)
    ew_demand_vph: float = Field(default=500, ge=100, le=1500)

    @model_validator(mode="after")
    def feasible(self):
        if self.cycle_seconds - self.lost_seconds - self.ns_green_seconds < 10:
            raise ValueError("Both approaches require at least 10 seconds green")
        return self


class AnalyzeRequest(Model):
    area: Area
    mode: Literal["demo", "sumo"] = "demo"
    inputs: Inputs = Field(default_factory=Inputs)
    layers: list[Layer] = Field(default_factory=lambda: ["roads"], max_length=8)
    analysis: AnalysisOptions = Field(default_factory=AnalysisOptions)
    data_as_of: datetime | None = None


class Provenance(Model):
    source: Literal["synthetic-demo"] = "synthetic-demo"
    source_version: str = "demo-2"
    method: str = "uniform-arrival delay plus synthetic capacity penalty"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    crs: str = "EPSG:4326"


class Uncertainty(Model):
    kind: str = "synthetic_model"
    description: str = "Synthetic illustrative estimate; uncalibrated and not an Iași measurement."
    interval: tuple[float, float] | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class Measurement(Model):
    value: float | None
    unit: str = "second/vehicle"
    status: Literal["estimated", "unknown"] = "estimated"
    provenance: list[Provenance] = Field(default_factory=lambda: [Provenance()])
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)


class Indicator(Measurement):
    id: str
    label: str


class Issue(Model):
    id: str = "signal_balance"
    summary: str = "Explore green-time allocation at a synthetic two-phase intersection."
    label: str = "DEMO — alocarea timpului verde"
    geometry: Point | None = None
    provenance: list[Provenance] = Field(default_factory=lambda: [Provenance()])
    uncertainty: Uncertainty = Field(default_factory=Uncertainty)
    indicator_ids: list[str] = ["ns_delay", "ew_delay", "mean_delay"]
    status: Literal["estimated"] = "estimated"


class LayerAvailability(Model):
    layer: Layer
    status: Literal["unknown"] = "unknown"
    reason: str = "No geographic layer acquired; this analysis uses synthetic intersection inputs only."


class AnalysisResponse(Model):
    analysis_id: str
    baseline_id: str
    area: Area
    created_at: datetime
    mode: Literal["demo"] = "demo"
    inputs: Inputs
    provenance: list[Provenance] = Field(default_factory=lambda: [Provenance()])
    indicators: list[Indicator]
    layer_availability: list[LayerAvailability] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=lambda: [Issue()])
    warnings: list[str] = ["DEMO: synthetic inputs, no real traffic measurements or SUMO run."]


class Parameters(Model):
    ns_green_seconds: float = Field(ge=10, le=160)


class Units(Model):
    ns_green_seconds: Literal["second"] = "second"


class Intervention(Model):
    type: Literal["signal_timing"] = "signal_timing"
    parameters: Parameters
    geometry: Point | None = None
    parameter_units: Units = Field(default_factory=Units)
    affected_feature_ids: list[Literal["demo-signal"]] = Field(default_factory=lambda: ["demo-signal"], min_length=1, max_length=1)


class Constraints(Model):
    minimum_green_seconds: Literal[10] = 10
    cycle_and_lost_time_fixed: Literal[True] = True


class AffectedAreaLimit(Model):
    value: float = Field(gt=0, le=500)
    unit: Literal["hectare"] = "hectare"


class ProposalConstraints(Model):
    max_affected_area: AffectedAreaLimit | None = None


class ProposeRequest(Model):
    analysis_id: str
    issue_id: str = Field(default="signal_balance", max_length=100)
    intervention_catalog_version: Literal["catalog-1"] = "catalog-1"
    requested_alternatives: list[Literal["minimal", "moderate", "transformative"]] = Field(default_factory=lambda: ["minimal", "moderate", "transformative"], min_length=1, max_length=3)
    area: AreaRef | None = None
    constraints: ProposalConstraints = Field(default_factory=ProposalConstraints)
    parameters: Parameters | None = None


class Validation(Model):
    status: Literal["accepted"] = "accepted"
    checks: list[str] = ["supported_demo_type", "parameters_valid", "fixed_cycle", "minimum_green", "no_land_take"]


class ExpectedImpact(Measurement):
    indicator_id: str
    direction: Literal["increase", "decrease", "unchanged"]


class Alternative(Model):
    level: str
    summary: str
    interventions: list[Intervention]
    rationale: str
    expected_impacts: list[ExpectedImpact] = Field(default_factory=list)
    validation: Validation = Field(default_factory=Validation)
    constraints: Constraints = Field(default_factory=Constraints)
    assumptions: list[str] = ["Two synthetic phases; demand, cycle and lost time remain fixed."]


class RecommendationModel(Model):
    provider: Literal["deterministic"] = "deterministic"
    model_id: Literal["signal-catalog-1"] = "signal-catalog-1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProposalResponse(Model):
    proposal_set_id: str
    analysis_id: str
    baseline_id: str
    model: RecommendationModel = Field(default_factory=RecommendationModel)
    alternatives: list[Alternative]
    rejected_alternatives: list[str] = Field(default_factory=list)
    warnings: list[str] = ["No LLM or simulation used. Feasibility applies only to the demo intersection."]


class TrafficSimulation(Model):
    requested: bool = False
    mode: Literal["none", "live", "offline", "replay"] = "none"
    replay_id: str | None = None

    @model_validator(mode="after")
    def consistent(self):
        if self.requested != (self.mode != "none"):
            raise ValueError("requested must agree with mode")
        if (self.mode == "replay") != (self.replay_id is not None):
            raise ValueError("replay_id is required only for replay mode")
        return self


class EvaluationOptions(Model):
    indicators: list[str] = Field(default_factory=list, max_length=30)
    traffic_simulation: TrafficSimulation = Field(default_factory=TrafficSimulation)


class EvaluateRequest(Model):
    analysis_id: str
    baseline_id: str
    proposal_set_id: str
    alternative_level: Literal["minimal", "moderate", "transformative"]
    interventions: list[Intervention] = Field(min_length=1, max_length=1)
    area: AreaRef | None = None
    evaluation: EvaluationOptions = Field(default_factory=EvaluationOptions)


class Comparison(Model):
    indicator_id: str
    baseline: Measurement
    scenario: Measurement
    delta: Measurement
    percent_change: float | None
    impact: Literal["improved", "worsened", "unchanged", "unknown"]


class Reference(Model):
    id: str
    source_snapshot: str = "synthetic-demo-2"
    intervention_catalog_version: str = "catalog-1"


class SimulationStatus(Model):
    status: Literal["not_requested"] = "not_requested"
    mode: Literal["none"] = "none"
    run_id: None = None
    simulator: None = None
    started_at: None = None
    completed_at: None = None
    configuration: None = None
    measurements: list[Indicator] = Field(default_factory=list)


class EvaluationResponse(Model):
    evaluation_id: str
    scenario_id: str
    created_at: datetime
    baseline: Reference
    scenario: Reference
    baseline_inputs: Inputs
    scenario_inputs: Inputs
    comparisons: list[Comparison]
    simulation: SimulationStatus = Field(default_factory=SimulationStatus)
    warnings: list[str] = ["DEMO estimates only. Negative and positive impacts use unchanged synthetic demand."]


class ErrorDetail(Model):
    field: str
    reason: str


class ErrorInfo(Model):
    code: str
    message: str
    details: list[ErrorDetail]
    request_id: str


class ErrorResponse(Model):
    error: ErrorInfo


class City(Model):
    id: str = "iasi-ro"
    name: str = "Iași"
    crs_default: str = "EPSG:4326"


class AreaBookmark(Model):
    id: str
    slug: str
    name: str
    center: tuple[float, float]
    bbox: None = None
    area_hectares: None = None
    population_estimate: None = None
    validation_status: Literal["demo_bookmark"] = "demo_bookmark"
    active_sensors_count: None = None


class AreasResponse(Model):
    city: City = Field(default_factory=City)
    areas: list[AreaBookmark]
    warnings: list[str] = ["DEMO bookmarks only; verified boundaries and sensor counts are unavailable."]
