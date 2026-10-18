"""Strictly validate untrusted proposal objects against SIM evidence."""

from __future__ import annotations

import json
import hashlib
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from shapely.geometry import LineString, Point, shape

from .geo import OSMData, _source_area_geometry_hash
from .proposal_catalog import get_intervention_catalog


_SCHEMA_FAILURES = {
    "proposal_not_object", "proposal_not_json_finite", "missing_candidate_id", "missing_intervention",
    "missing_parameters", "invalid_coordinates", "unsupported_units",
}
_ALLOWED_UNITS = {"EPSG:4326", "m", "km", "m/s", "s", "min", "boolean", "ratio", "node", "route_pair"}
_COST_KEYS = {"cost", "construction_cost", "estimated_cost", "construction_cost_estimate", "cost_estimate", "budget"}
_CITATION_KEYS = {"source_citations", "citations"}
_UNSUPPORTED_PHYSICAL_TEXT = re.compile(r"\b(?:feasible|buildable|construction[- ]ready|safe to build|approved for construction)\b", re.IGNORECASE)
_UNSUPPORTED_COST_TEXT = re.compile(r"(?:€|\$|\b(?:lei|RON|EUR)\b|\b(?:low[- ]cost|estimated cost|construction cost is)\b)", re.IGNORECASE)


def _canonical(value: Any) -> str | None:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        return None


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key).casefold(), item
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def _coordinate(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        return None
    longitude, latitude = float(value[0]), float(value[1])
    if not math.isfinite(longitude) or not math.isfinite(latitude):
        return None
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        return None
    return longitude, latitude


def _candidate_records(candidates: Any) -> list[Mapping[str, Any]]:
    if isinstance(candidates, Mapping):
        values = candidates.get("ranked_candidates", candidates.get("options", []))
    else:
        values = candidates
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return [value for value in values if isinstance(value, Mapping)]


def _allowed_citations(data: OSMData, candidate: Mapping[str, Any] | None) -> set[str]:
    allowed = set()
    for value in (data.metadata.get("source"), data.metadata.get("source_version"), data.metadata.get("retrieved_at")):
        if isinstance(value, str) and value:
            allowed.add(value)
    if candidate:
        provenance = candidate.get("provenance", [])
        for key, value in _walk(provenance):
            if key in {"source", "source_version", "retrieved_at", "method", "crs"} and isinstance(value, str):
                allowed.add(value)
    return allowed


def _unit_findings(value: Any) -> list[str]:
    invalid = []
    for key, item in _walk(value):
        if key in {"unit", "units"}:
            units = list(item.values()) if isinstance(item, Mapping) else item if isinstance(item, list) else [item]
            for unit in units:
                if unit is None:
                    continue
                if isinstance(unit, str) and unit not in _ALLOWED_UNITS:
                    invalid.append(unit)
                elif not isinstance(unit, str):
                    invalid.append(str(unit))
        elif key == "parameter_units" and isinstance(item, Mapping):
            for unit in item.values():
                if not isinstance(unit, str) or unit not in _ALLOWED_UNITS:
                    invalid.append(str(unit))
    return sorted(set(invalid))


def _set_status(result: dict[str, Any]) -> None:
    codes = {item["code"] for item in result["findings"]}
    schema_valid = not bool(codes & _SCHEMA_FAILURES)
    action_failures = _SCHEMA_FAILURES | {
        "unsupported_intervention_type", "candidate_not_found", "candidate_intervention_mismatch",
        "invalid_geometry", "geometry_outside_study_area", "modeled_connection_not_evaluated", "stale_source_evidence",
    }
    support = result["intervention_type"] in {item["type_id"] for item in get_intervention_catalog()["supported_interventions"]} and not bool(codes & action_failures)
    has_errors = bool(result["findings"])
    evaluated = support and result.get("candidate_evaluation_available", False)
    result["schema_status"] = "schema_valid_concept" if schema_valid else "invalid_schema"
    result["support_status"] = "supported_executable_intervention" if support else "unsupported_or_unmatched"
    result["evaluation_status"] = "evaluated_model_scenario" if evaluated else "not_evaluated"
    result["physical_feasibility"] = "unknown"
    result["status"] = "rejected" if has_errors else ("candidate_backed_evaluated" if evaluated else "schema_valid_concept_only")


def validate_proposal(
    proposal: Any,
    *,
    data: OSMData,
    candidate_evaluation: Any,
    verified_simulation_run_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Classify a proposal without treating valid JSON as evaluation or approval."""
    findings: list[dict[str, str]] = []

    def add(code: str, message: str, field: str = "proposal") -> None:
        item = {"code": code, "field": field, "message": message}
        if item not in findings:
            findings.append(item)

    if not isinstance(proposal, Mapping):
        add("proposal_not_object", "Proposal must be a JSON object.")
        result = {"status": "rejected", "schema_status": "invalid_schema", "support_status": "unsupported_or_unmatched", "evaluation_status": "not_evaluated", "physical_feasibility": "unknown", "source_area_verification": "unknown", "candidate_id": None, "intervention_type": None, "findings": findings, "candidate_evaluation_available": False}
        return result
    if _canonical(proposal) is None:
        add("proposal_not_json_finite", "Proposal must contain only finite JSON-compatible values.")

    candidate_id = proposal.get("candidate_id")
    data_source = str(data.metadata.get("source", "unknown"))
    source_version = str(data.metadata.get("source_version", "unknown"))
    source_area = data.metadata.get("source_area", {})
    cache_metadata = data.metadata.get("cache", {})
    if "fixture" in data_source.casefold() or "fixture" in source_version.casefold():
        source_area_verification = "synthetic_fixture"
    elif (isinstance(cache_metadata, Mapping) and cache_metadata.get("area_equivalence_verified") is False) or (isinstance(source_area, Mapping) and source_area.get("equivalence_verified") is False):
        source_area_verification = "unverified"
    elif data_source == "OpenStreetMap":
        source_area_verification = "verified"
    else:
        source_area_verification = "unknown"

    evaluation = candidate_evaluation if isinstance(candidate_evaluation, Mapping) else {}
    evaluation_area_id = evaluation.get("area_id")
    if evaluation_area_id and str(evaluation_area_id) != data.area.area_id:
        add("stale_source_evidence", "Candidate evaluation belongs to a different study area than the supplied source snapshot.", "candidate_evaluation.area_id")
    evaluation_geometry_hash = evaluation.get("study_area_geometry_sha256")
    if not evaluation_geometry_hash:
        baseline = evaluation.get("baseline_analysis", {})
        area_record = baseline.get("area", {}) if isinstance(baseline, Mapping) else {}
        boundary = area_record.get("boundary") if isinstance(area_record, Mapping) else None
        if boundary:
            try:
                evaluation_geometry_hash = hashlib.sha256(shape(boundary).normalize().wkb).hexdigest()
            except Exception:
                evaluation_geometry_hash = None
    if evaluation_geometry_hash and evaluation_geometry_hash != _source_area_geometry_hash(data.area):
        add("stale_source_evidence", "Candidate evaluation source polygon does not match the supplied source snapshot.", "candidate_evaluation.study_area_geometry_sha256")
    baseline_source = evaluation.get("baseline_analysis", {})
    evaluated_provenance = baseline_source.get("provenance", {}) if isinstance(baseline_source, Mapping) else {}
    if isinstance(evaluated_provenance, Mapping):
        for key in ("source", "source_version", "retrieved_at"):
            evaluated_value = evaluated_provenance.get(key)
            current_value = data.metadata.get(key)
            if evaluated_value is not None and current_value is not None and evaluated_value != current_value:
                add("stale_source_evidence", f"Candidate evaluation {key} does not match the supplied source snapshot.", f"candidate_evaluation.baseline_analysis.provenance.{key}")
    if not isinstance(candidate_id, str) or not candidate_id:
        add("missing_candidate_id", "A candidate ID from a completed SIM evaluation is required.", "candidate_id")
        candidate_id = None
    intervention = proposal.get("intervention")
    if not isinstance(intervention, Mapping):
        add("missing_intervention", "An executable intervention object is required.", "intervention")
        intervention = {}
    kind = intervention.get("type")
    kind = kind if isinstance(kind, str) else None
    supported = {item["type_id"]: item for item in get_intervention_catalog()["supported_interventions"]}
    candidate_items = _candidate_records(candidate_evaluation)
    candidate = next((item for item in candidate_items if item.get("candidate_id") == candidate_id), None)
    if kind not in supported:
        add("unsupported_intervention_type", f"Intervention type {kind or '<missing>'} is not implemented by SIM.", "intervention.type")
    else:
        required = {item["name"] for item in supported[kind]["required_parameters"]}
        missing = sorted(name for name in required if name not in intervention)
        if missing:
            add("missing_parameters", "Required intervention parameters are missing: " + ", ".join(missing) + ".", "intervention")

    invalid_units = _unit_findings(proposal)
    if invalid_units:
        add("unsupported_units", "Proposal uses unsupported measurement units: " + ", ".join(invalid_units) + ".", "units")

    if kind == "add_pedestrian_connection":
        start = _coordinate(intervention.get("start"))
        end = _coordinate(intervention.get("end"))
        if start is None or end is None:
            add("invalid_coordinates", "start and end must be finite EPSG:4326 [longitude, latitude] positions.", "intervention.start/end")
        else:
            start_point, end_point = Point(start), Point(end)
            line = LineString([start, end])
            if not data.area.polygon.covers(start_point) or not data.area.polygon.covers(end_point) or not data.area.polygon.covers(line):
                add("geometry_outside_study_area", "Both endpoints and their connecting segment must lie inside the selected study area.", "intervention")
    elif kind == "set_connection_enabled" and candidate is None:
        add("modeled_connection_not_evaluated", "A connection toggle must match a candidate or scenario actually evaluated by SIM.", "candidate_id")

    if candidate_id and candidate is None:
        add("candidate_not_found", "Candidate ID is not present in the supplied evaluated candidate set.", "candidate_id")
    if candidate is not None:
        expected = candidate.get("intervention")
        if not isinstance(expected, Mapping) or dict(expected) != dict(intervention):
            add("candidate_intervention_mismatch", "Intervention parameters and geometry must exactly match the selected evaluated candidate.", "intervention")
        impact = candidate.get("impact")
        candidate_evaluation_available = isinstance(impact, Mapping) and isinstance(impact.get("aggregate"), Mapping)
    else:
        candidate_evaluation_available = False

    allowed_citations = _allowed_citations(data, candidate)
    for key, value in _walk(proposal):
        explicitly_unsupported_cost = isinstance(value, Mapping) and value.get("status") == "unsupported" and value.get("value") is None
        if key in _COST_KEYS and value not in (None, "") and not explicitly_unsupported_cost:
            add("unsupported_cost_claim", "SIM has no construction-cost evaluator; cost claims are not accepted.", key)
        if key in _CITATION_KEYS:
            citations = value if isinstance(value, list) else [value]
            for citation in citations:
                if not isinstance(citation, str) or citation not in allowed_citations:
                    add("fabricated_or_unverified_source_citation", "Citation is not present in the supplied SIM provenance.", key)
        if key in {"simulation_run_id", "sumo_run_id", "run_id"} and value not in (None, ""):
            if not isinstance(value, str) or value not in set(verified_simulation_run_ids):
                add("invented_simulation_run_id", "Simulation run ID is not present in the verified run set.", key)
        if key in {"observed_metrics", "observations"} and value not in (None, [], {}):
            add("unsupported_observed_metrics", "This graph evaluation contains no observed travel or traffic measurements.", key)
        if key in {"physical_feasibility", "buildability", "construction_ready", "safety_approved"} and value not in (None, "", "unknown"):
            add("unsupported_physical_feasibility_claim", "Physical feasibility remains unknown without field, ownership, accessibility, and safety evidence.", key)
        if key in {"summary", "rationale", "description", "claim"} and isinstance(value, str):
            if _UNSUPPORTED_PHYSICAL_TEXT.search(value):
                add("unsupported_physical_feasibility_claim", "Proposal text asserts physical feasibility that SIM has not established.", key)
            if _UNSUPPORTED_COST_TEXT.search(value):
                add("unsupported_cost_claim", "Proposal text asserts a construction cost that SIM has not evaluated.", key)
        if key in {"epistemic_status", "evidence_status"} and isinstance(value, str) and value.casefold() == "observed":
            add("unsupported_observed_metrics", "No observed traffic metric is available to support this proposal claim.", key)
        if key == "status" and isinstance(value, str):
            normalized_status = value.casefold()
            if normalized_status in {"validated", "accepted", "approved", "buildable"}:
                add("untrusted_validation_claim", "Input validation labels are untrusted; SIM assigns status from checks and evaluation evidence.", key)
            if normalized_status in {"observed", "measured"}:
                add("unsupported_observed_metrics", "No observed traffic metric is available to support this proposal claim.", key)

    result = {
        "candidate_id": candidate_id,
        "intervention_type": kind,
        "findings": findings,
        "candidate_evaluation_available": candidate_evaluation_available,
        "source_area_verification": source_area_verification,
    }
    _set_status(result)
    result.pop("candidate_evaluation_available", None)
    return result


def validate_proposal_set(
    proposals: Any,
    *,
    data: OSMData,
    candidate_evaluation: Any,
    verified_simulation_run_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Validate a set and mark later duplicate actions as rejected."""
    if not isinstance(proposals, Sequence) or isinstance(proposals, (str, bytes)):
        proposals = []
    run_ids = tuple(verified_simulation_run_ids)
    results = []
    seen: set[str] = set()
    for proposal in proposals:
        result = validate_proposal(proposal, data=data, candidate_evaluation=candidate_evaluation, verified_simulation_run_ids=run_ids)
        signature = _canonical(proposal.get("intervention")) if isinstance(proposal, Mapping) else None
        if signature is not None and signature in seen:
            finding = {"code": "duplicate_intervention", "field": "intervention", "message": "The same intervention appears more than once in this proposal set."}
            if finding not in result["findings"]:
                result["findings"].append(finding)
            _set_status(result)
        elif signature is not None:
            seen.add(signature)
        results.append(result)
    return {
        "schema_version": 1,
        "status": "completed_with_rejections" if any(item["status"] == "rejected" for item in results) else "all_candidate_backed_evaluated",
        "results": results,
        "summary": {
            "submitted_count": len(results),
            "accepted_count": sum(item["status"] == "candidate_backed_evaluated" for item in results),
            "rejected_count": sum(item["status"] == "rejected" for item in results),
            "duplicate_count": sum(any(finding["code"] == "duplicate_intervention" for finding in item["findings"]) for item in results),
        },
    }
