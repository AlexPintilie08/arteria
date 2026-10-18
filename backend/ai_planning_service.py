"""Orchestrate stored SIM evidence through the SIM-owned AI validator."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import sim

from backend.ai_provider import resolve_provider
from backend.ai_planning_models import AIPlanningResult
from backend.spatial_models import Study


class InvalidPlanningPacket(Exception):
    pass


def verify_study_packet(study: Study) -> tuple[dict[str, Any], str]:
    packet = study.ai_evidence_packet
    if not isinstance(packet, dict) or not packet:
        raise InvalidPlanningPacket("This stored study does not contain an AI planning packet.")
    integrity = packet.get("integrity")
    if not isinstance(integrity, dict):
        raise InvalidPlanningPacket("Stored AI planning packet integrity is unavailable.")
    digest = integrity.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64 or study.evidence_packet_sha256 != digest:
        raise InvalidPlanningPacket("Stored AI planning packet hash does not match the study.")

    area_id = packet.get("study_area", {}).get("area_id") if isinstance(packet.get("study_area"), dict) else None
    if not isinstance(area_id, str) or not area_id:
        raise InvalidPlanningPacket("Stored AI planning packet area is unavailable.")
    # A fully empty, correctly bound response exercises SIM's packet schema,
    # byte limit, checksum, area identity, and cross-context consistency checks.
    packet_probe = {
        "schema_version": "arteria.ai-planning-response.v1",
        "area_id": area_id,
        "evidence_packet_sha256": digest,
        "summary": "",
        "identified_problems": [],
        "recommended_solutions": [],
        "supported_candidate_ids": [],
        "evidence_references": [],
        "limitations": [],
        "requires_field_verification": True,
    }
    validation = sim.validate_ai_planning_response(packet_probe, packet)
    if validation.get("status") != "validated":
        raise InvalidPlanningPacket("Stored AI planning packet failed SIM integrity validation.")
    return packet, digest


def create_planning_result(
    study: Study,
    packet: dict[str, Any],
    packet_sha256: str,
    planning_id: str,
) -> AIPlanningResult:
    provider = resolve_provider()
    outcome = sim.run_ai_planning(
        packet,
        provider.call_model,
        timeout_seconds=provider.timeout_seconds,
    )
    validation = outcome.get("validation")
    validated = validation if isinstance(validation, dict) else None
    generated = outcome.get("ai_generated") is True
    status = outcome.get("status")
    warnings = list(study.warnings)
    warnings.append("AI planning interprets stored SIM evidence; it does not execute SUMO or determine physical feasibility.")
    if not generated:
        warnings.append("No cloud model response was received; no AI recommendation is available.")

    urban = packet.get("urban_intelligence", {})
    area_id = urban.get("area_id") if isinstance(urban, dict) else None
    return AIPlanningResult(
        planning_id=planning_id,
        study_id=study.study_id,
        baseline_id=study.baseline_id,
        source=study.source,
        area_id=area_id,
        engine_revision=study.engine_revision,
        calculation=study.calculation,
        evidence_packet_sha256=packet_sha256,
        provider_status=status,
        provider=provider.provider_id if generated else None,
        model_id=provider.model_id if generated else None,
        ai_generated=generated,
        summary=(validated.get("summary") if validated else None),
        identified_problems=(validated.get("identified_problems", []) if validated else []),
        recommended_solutions=(validated.get("recommended_solutions", []) if validated else []),
        validation=validated,
        error_code=(provider.unavailable_code or outcome.get("error_code")),
        created_at=datetime.now(timezone.utc),
        warnings=warnings,
    )
