"""Validate consumed engine fields without rewriting the engine's JSON payload."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EngineModel(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True, allow_inf_nan=False)


Identifier = Annotated[str, Field(min_length=1)]
Count = Annotated[int, Field(ge=0)]


class Intervention(EngineModel):
    type: Literal["add_pedestrian_connection"]
    start: list[float]
    end: list[float]

    @field_validator("start", "end")
    @classmethod
    def coordinate(cls, value):
        if len(value) != 2 or not -180 <= value[0] <= 180 or not -90 <= value[1] <= 90:
            raise ValueError("Expected longitude and latitude")
        return value


class RouteState(EngineModel):
    status: str
    network_distance_m: float | None
    estimated_walk_time_s: float | None


class Route(EngineModel):
    origin_node_id: Identifier
    destination_node_id: Identifier
    outcome: str
    before: RouteState
    after: RouteState
    distance_delta_m: float | None


class Aggregate(EngineModel):
    evaluated_pair_count: Count
    improved_count: Count
    regressed_count: Count
    newly_reachable_count: Count
    newly_unreachable_count: Count
    total_distance_savings_m: float


class Impact(EngineModel):
    aggregate: Aggregate
    routes: list[Route]
    provenance: dict
    warnings: list[str]


class Candidate(EngineModel):
    candidate_id: Identifier
    intervention: Intervention
    impact: Impact
    evaluation_rationale: list[str]
    ranking_explanation: str
    rank: Annotated[int, Field(ge=1)]


class Alternatives(EngineModel):
    ranked_candidates: list[Candidate]

    @field_validator("ranked_candidates")
    @classmethod
    def unique_ids(cls, candidates):
        if len({c.candidate_id for c in candidates}) != len(candidates):
            raise ValueError("Duplicate candidate identifiers")
        return candidates


class Analysis(EngineModel):
    analysis_id: Identifier
    area: dict
    created_at: str
    indicators: list[dict]
    issues: list[dict]
    provenance: dict
    warnings: list[str]


class EngineResult(EngineModel):
    analysis: Analysis
    alternatives: Alternatives
    urban_issues: dict | None = None
    solution_plan: dict | None = None
    ai_evidence_packet: dict | None = None
    problem_locations_geojson: dict | None = None


def reject_nonfinite(value):
    raise ValueError("Non-finite JSON number")
