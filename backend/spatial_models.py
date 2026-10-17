"""Versioned graph-engine envelope; native evidence and GeoJSON stay intact."""
from datetime import datetime
from typing import Literal
from pydantic import Field, JsonValue, model_validator
from backend.models import Model


class SpatialRequest(Model):
    source: Literal["fixture", "osm"] = "fixture"
    neighborhood_id: str | None = Field(default=None, min_length=1, max_length=200)
    sample_count: int = Field(default=16, ge=1, le=64, strict=True)
    max_candidates: int = Field(default=3, ge=1, le=3, strict=True)
    seed: str = Field(default="arteria-spatial-v1", min_length=1, max_length=100)

    @model_validator(mode="after")
    def source_area(self):
        if self.source == "fixture" and self.neighborhood_id is not None:
            raise ValueError("Fixture has its own synthetic area; do not attach a sourced neighborhood")
        if self.source == "osm" and self.neighborhood_id is None:
            raise ValueError("OSM analysis requires a SIM neighborhood catalog ID")
        return self


class Study(Model):
    study_id: str
    baseline_id: str
    created_at: datetime
    source: Literal["fixture", "osm"]
    engine_revision: str
    calculation: Literal["pedestrian_graph"] = "pedestrian_graph"
    analysis: dict[str, JsonValue]
    alternatives: dict[str, JsonValue]
    proposal_options: list[dict[str, JsonValue]] = Field(default_factory=list)
    proposal_validation: dict[str, JsonValue] = Field(default_factory=dict)
    evidence_packet: dict[str, JsonValue] = Field(default_factory=dict)
    warnings: list[str]


class Selection(Model):
    baseline_id: str
    candidate_id: str = Field(min_length=1, max_length=200)
    intervention: dict[str, JsonValue]


class Candidates(Model):
    study_id: str
    baseline_id: str
    candidates: list[dict[str, JsonValue]]
    warnings: list[str]


class SpatialEvaluation(Model):
    study_id: str
    baseline_id: str
    candidate_id: str
    source: Literal["fixture", "osm"]
    evaluated_at: datetime
    execution: Literal["stored_graph_comparison"] = "stored_graph_comparison"
    sumo_executed: Literal[False] = False
    intervention: dict[str, JsonValue]
    impact: dict[str, JsonValue]
    proposal_validation: dict[str, JsonValue]
    warnings: list[str]
