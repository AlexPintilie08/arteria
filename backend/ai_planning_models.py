"""Strict HTTP models for persisted SIM-grounded AI planning results."""

from datetime import datetime
from typing import Literal

from pydantic import Field, JsonValue

from backend.models import Model


PlanningStatus = Literal[
    "provider_unavailable",
    "timeout",
    "provider_error",
    "invalid_response",
    "completed_with_rejections",
    "completed",
]


class PlanningRequest(Model):
    """Planning currently accepts no client-authored evidence or instructions."""


class AIPlanningResult(Model):
    planning_id: str
    study_id: str
    baseline_id: str
    source: Literal["fixture", "osm"]
    area_id: str
    engine_revision: str
    calculation: Literal["pedestrian_graph"]
    evidence_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_status: PlanningStatus
    provider: str | None = None
    model_id: str | None = None
    ai_generated: bool
    summary: str | None = None
    identified_problems: list[dict[str, JsonValue]] = Field(default_factory=list)
    recommended_solutions: list[dict[str, JsonValue]] = Field(default_factory=list)
    validation: dict[str, JsonValue] | None = None
    error_code: str | None = Field(default=None, max_length=100)
    created_at: datetime
    warnings: list[str]
