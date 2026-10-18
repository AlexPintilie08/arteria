"""Provider-neutral, bounded AI planning input and strict response validation."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import math
import re
from collections.abc import Callable, Mapping
from typing import Any

from .geo import OSMData, _source_area_geometry_hash
from .proposal_context import build_proposal_context


AI_PACKET_SCHEMA = "arteria.ai-planning-packet.v1"
AI_RESPONSE_SCHEMA = "arteria.ai-planning-response.v1"
MAX_AI_PACKET_BYTES = 65_536
MAX_AI_RESPONSE_BYTES = 16_384
MAX_AI_PROBLEMS = 12
MAX_AI_SOLUTIONS = 24

AI_SYSTEM_PROMPT = """You are an evidence-grounded urban planning assistant for ARTERIA, invoked by the backend's configured cloud model.

Analyze only the supplied SIM evidence. Identify the strongest supported problems and explain their significance, then select relevant solution IDs from the supplied solution plan. Use only the supplied problem IDs, solution IDs, candidate IDs, and evidence IDs. Return strict JSON that matches the supplied schema exactly.

Do not invent data, coordinates, geometry, metrics, traffic volumes, construction costs, citations, source IDs, SUMO run IDs, accident statistics, population counts, measured congestion, simulation results, or physical feasibility. Do not assert that a graph gap is a confirmed barrier. Do not call a calculated route dangerous. Distinguish graph calculations, candidate-specific diagnostics, and SUMO outputs under synthetic demand. Candidate-specific diagnostic impact is not shared-sample ranking benefit.

The SIM solution plan already carries authoritative intervention geometry, candidate validation, evaluation status, and numerical impacts. Your response must refer to its solution IDs and may not restate or alter those authoritative fields. A conceptual solution has no executable action or calculated benefit. If evidence is weak, choose a field or data review concept, explain uncertainty, or return no recommendation. Do not add solutions to reach a count. Always require field verification where physical infrastructure is involved."""

AI_OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ARTERIA SIM AI planning response",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version", "area_id", "evidence_packet_sha256", "summary", "identified_problems",
        "recommended_solutions", "supported_candidate_ids", "evidence_references", "limitations",
        "requires_field_verification",
    ],
    "properties": {
        "schema_version": {"const": AI_RESPONSE_SCHEMA},
        "area_id": {"type": "string", "minLength": 1, "maxLength": 200},
        "evidence_packet_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "summary": {"type": "string", "maxLength": 1200},
        "identified_problems": {
            "type": "array", "maxItems": MAX_AI_PROBLEMS,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["problem_id", "explanation", "evidence_ids"],
                "properties": {
                    "problem_id": {"type": "string", "maxLength": 100},
                    "explanation": {"type": "string", "maxLength": 700},
                    "evidence_ids": {"type": "array", "maxItems": 8, "uniqueItems": True, "items": {"type": "string", "maxLength": 120}},
                },
            },
        },
        "recommended_solutions": {
            "type": "array", "maxItems": MAX_AI_SOLUTIONS,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["solution_id", "candidate_id", "problem_ids", "title", "explanation", "expected_benefit_type", "evidence_ids", "field_verification_required"],
                "properties": {
                    "solution_id": {"type": "string", "maxLength": 100},
                    "candidate_id": {"type": ["string", "null"], "maxLength": 120},
                    "problem_ids": {"type": "array", "maxItems": 8, "uniqueItems": True, "items": {"type": "string", "maxLength": 100}},
                    "title": {"type": "string", "maxLength": 180},
                    "explanation": {"type": "string", "maxLength": 700},
                    "expected_benefit_type": {"type": "string", "maxLength": 100},
                    "evidence_ids": {"type": "array", "maxItems": 8, "uniqueItems": True, "items": {"type": "string", "maxLength": 120}},
                    "field_verification_required": {"type": "boolean"},
                },
            },
        },
        "supported_candidate_ids": {"type": "array", "maxItems": 8, "uniqueItems": True, "items": {"type": "string", "maxLength": 120}},
        "evidence_references": {"type": "array", "maxItems": 96, "uniqueItems": True, "items": {"type": "string", "maxLength": 120}},
        "limitations": {"type": "array", "maxItems": 12, "items": {"type": "string", "maxLength": 500}},
        "requires_field_verification": {"const": True},
    },
}

_TOP_FIELDS = set(AI_OUTPUT_SCHEMA["required"])
_PROBLEM_FIELDS = {"problem_id", "explanation", "evidence_ids"}
_SOLUTION_FIELDS = {"solution_id", "candidate_id", "problem_ids", "title", "explanation", "expected_benefit_type", "evidence_ids", "field_verification_required"}
_NUMBER_TEXT = re.compile(r"\d|(?:€|\$|\b(?:lei|RON|EUR|USD)\b)|https?://|www\.", re.IGNORECASE)
_UNSUPPORTED_CLAIM = re.compile(r"\b(?:feasible|buildable|construction[- ]ready|safe to build|approved for construction|legally approved|construction costs?|cost estimate|budget|measured congestion|observed traffic|population count|resident count|accident statistics)\b", re.IGNORECASE)
_POSITIVE_IMPACT_TEXT = re.compile(r"\b(?:improv\w*|reduc\w*|sav\w*|shorten\w*|increase\w*\s+(?:access|reachability)|benefit\w*)\b", re.IGNORECASE)
_NO_IMPACT_TEXT = re.compile(r"\b(?:no|zero|unchanged|without)\s+(?:(?:measurable|calculated|shared-sample)\s+)?(?:impact|benefit|improvement|change|savings?)\b", re.IGNORECASE)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _parse_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON value {value} is not allowed.")


def _string_list(value: Any, *, maximum_items: int, maximum_length: int, nonempty: bool = False, unique: bool = True) -> bool:
    if not isinstance(value, list) or len(value) > maximum_items or (nonempty and not value):
        return False
    if any(not isinstance(item, str) or len(item) > maximum_length for item in value):
        return False
    return not unique or len(set(value)) == len(value)


def _packet_digest(packet: Mapping[str, Any]) -> str:
    body = {key: value for key, value in packet.items() if key != "integrity"}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


def _compact_problem(problem: Mapping[str, Any]) -> dict[str, Any]:
    evidence = []
    for item in problem.get("evidence", []) if isinstance(problem.get("evidence"), list) else []:
        if isinstance(item, Mapping):
            evidence.append(dict(item))
    output = {
        key: problem.get(key)
        for key in ("problem_id", "problem_type", "title", "description", "location", "geometry", "geometry_meaning", "severity", "severity_basis", "data_confidence", "source", "source_area_verification", "related_candidate_ids", "limitations")
        if key in problem
    }
    output["evidence"] = evidence[:8]
    return output


def _compact_solution(solution: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: solution.get(key)
        for key in ("solution_id", "status", "solution_type", "title", "description", "problem_ids", "primary_problem_id", "candidate_id", "action_type", "expected_benefit_type", "evidence_ids", "field_verification_required", "physical_feasibility", "limitations")
        if key in solution
    }


def build_ai_planning_packet(
    data: OSMData,
    analysis: Mapping[str, Any],
    urban_issues: Mapping[str, Any],
    candidate_evaluation: Mapping[str, Any],
    solution_plan: Mapping[str, Any],
    *,
    max_packet_bytes: int = MAX_AI_PACKET_BYTES,
) -> dict[str, Any]:
    """Bind urban findings and the reusable proposal context into a bounded packet."""
    if isinstance(max_packet_bytes, bool) or not isinstance(max_packet_bytes, int) or not 4_096 <= max_packet_bytes <= MAX_AI_PACKET_BYTES:
        raise ValueError(f"max_packet_bytes must be an integer from 4096 through {MAX_AI_PACKET_BYTES}.")
    area_id = data.area.area_id
    if analysis.get("area", {}).get("area_id") != area_id or candidate_evaluation.get("area_id") != area_id or urban_issues.get("area_id") != area_id or solution_plan.get("area_id") != area_id:
        raise ValueError("All SIM inputs must refer to the same study area.")
    if urban_issues.get("area_geometry_sha256") != _source_area_geometry_hash(data.area):
        raise ValueError("Urban issue source geometry does not match the supplied OSMData area.")
    context_budget = max(1_024, max_packet_bytes - 24_000)
    context = build_proposal_context(data, analysis, candidate_evaluation, max_packet_bytes=context_budget)
    problems_raw = urban_issues.get("problems", [])
    solutions_raw = solution_plan.get("solutions", [])
    gaps_raw = urban_issues.get("coverage_gaps", [])
    observations_raw = urban_issues.get("simulation_observations", [])
    problems = [_compact_problem(item) for item in problems_raw if isinstance(item, Mapping)] if isinstance(problems_raw, list) else []
    solutions = [_compact_solution(item) for item in solutions_raw if isinstance(item, Mapping)] if isinstance(solutions_raw, list) else []
    gaps = [dict(item) for item in gaps_raw if isinstance(item, Mapping)] if isinstance(gaps_raw, list) else []
    observations = [dict(item) for item in observations_raw if isinstance(item, Mapping)] if isinstance(observations_raw, list) else []
    problem_total, solution_total = len(problems), len(solutions)
    gap_total, observation_total = len(gaps), len(observations)

    while True:
        included_problems = problems[:MAX_AI_PROBLEMS]
        included_gaps = gaps[:16]
        included_observations = observations[:4]
        included_problem_ids = {
            str(item.get("problem_id"))
            for item in included_problems
            if isinstance(item.get("problem_id"), str)
        }
        included_evidence_ids = {
            str(evidence.get("evidence_id"))
            for problem in included_problems
            for evidence in (problem.get("evidence", []) if isinstance(problem.get("evidence"), list) else [])
            if isinstance(evidence, Mapping) and isinstance(evidence.get("evidence_id"), str)
        }
        included_evidence_ids.update(
            str(item.get("gap_id")) for item in included_gaps
            if isinstance(item.get("gap_id"), str)
        )
        included_evidence_ids.update(
            str(item.get("observation_id")) for item in included_observations
            if isinstance(item.get("observation_id"), str)
        )
        included_solutions = []
        for solution in solutions[:MAX_AI_SOLUTIONS]:
            evidence_ids = solution.get("evidence_ids", [])
            problem_ids = solution.get("problem_ids", [])
            if (
                isinstance(evidence_ids, list)
                and evidence_ids
                and all(isinstance(value, str) for value in evidence_ids)
                and set(evidence_ids).issubset(included_evidence_ids)
                and isinstance(problem_ids, list)
                and all(isinstance(value, str) for value in problem_ids)
                and set(problem_ids).issubset(included_problem_ids)
            ):
                included_solutions.append(solution)
        body = {
            "schema_version": AI_PACKET_SCHEMA,
            "study_area": context["study_area"],
            "source": {
                "geographic_source": context.get("geographic_source", {}),
                "data_confidence": urban_issues.get("data_confidence"),
                "source_area_verification": urban_issues.get("source_area_verification"),
                "area_geometry_sha256": urban_issues.get("area_geometry_sha256"),
                "attribution": "© OpenStreetMap contributors" if urban_issues.get("source") == "OpenStreetMap" else urban_issues.get("source"),
                "license": "ODbL-1.0" if urban_issues.get("source") == "OpenStreetMap" else None,
            },
            "sim_proposal_context": context,
            "urban_intelligence": {
                "schema_version": urban_issues.get("schema_version"),
                "method_version": urban_issues.get("method_version"),
                "area_id": urban_issues.get("area_id"),
                "area_geometry_sha256": urban_issues.get("area_geometry_sha256"),
                "thresholds": urban_issues.get("thresholds", {}),
                "sample": urban_issues.get("sample", {}),
                "problems": included_problems,
                "omitted_problem_count": max(0, problem_total - len(included_problems)),
                "coverage_gaps": included_gaps,
                "omitted_coverage_gap_count": max(0, gap_total - len(included_gaps)),
                "simulation_observations": included_observations,
                "omitted_simulation_observation_count": max(0, observation_total - len(included_observations)),
                "simulation_status": urban_issues.get("simulation_status"),
                "warnings": list(urban_issues.get("warnings", []))[:16] if isinstance(urban_issues.get("warnings"), list) else [],
                "limitations": list(urban_issues.get("limitations", []))[:12] if isinstance(urban_issues.get("limitations"), list) else [],
            },
            "solution_plan": {
                "schema_version": solution_plan.get("schema_version"),
                "status": solution_plan.get("status"),
                "solutions": included_solutions,
                "omitted_solution_count": max(0, solution_total - len(included_solutions)),
                "candidate_validation": solution_plan.get("candidate_validation", {}),
            },
            "output_schema_version": AI_RESPONSE_SCHEMA,
            "truncation": {
                "packet_byte_limit": max_packet_bytes,
                "serialized_bytes": 0,
            },
        }
        body["truncation"]["serialized_bytes"] = len(_canonical(body).encode("utf-8"))
        packet = {**body, "integrity": {"sha256": _packet_digest(body), "serialized_bytes": 0}}
        for _ in range(3):
            packet["integrity"]["serialized_bytes"] = len(_canonical(packet).encode("utf-8"))
        final_size = len(_canonical(packet).encode("utf-8"))
        packet["integrity"]["serialized_bytes"] = final_size
        if final_size <= max_packet_bytes:
            return packet
        if len(problems) > 0:
            problems = problems[:-1]
        elif len(solutions) > 0:
            solutions = solutions[:-1]
        elif len(gaps) > 0:
            gaps = gaps[:-1]
        elif len(observations) > 0:
            observations = observations[:-1]
        else:
            raise ValueError("Core AI planning packet exceeds max_packet_bytes after bounded evidence truncation.")


def _text_findings(text: Any, *, maximum: int) -> list[str]:
    if not isinstance(text, str) or len(text) > maximum:
        return ["invalid_or_oversized_text"]
    findings = []
    if _NUMBER_TEXT.search(text):
        findings.append("untrusted_numeric_or_citation_claim")
    if _UNSUPPORTED_CLAIM.search(text):
        findings.append("unsupported_physical_or_observed_claim")
    return findings


def _reject(code: str, item_index: int | None = None) -> dict[str, Any]:
    result = {"status": "rejected", "code": code}
    if item_index is not None:
        result["item_index"] = item_index
    return result


def _candidate_impact_contradiction(item: Mapping[str, Any], candidate: Mapping[str, Any] | None) -> bool:
    if candidate is None:
        return False
    impact = candidate.get("shared_sample_impact")
    aggregate = impact.get("aggregate") if isinstance(impact, Mapping) else None
    narrative = f"{item.get('title', '')} {item.get('explanation', '')}"
    if not isinstance(aggregate, Mapping):
        return bool(_POSITIVE_IMPACT_TEXT.search(narrative))
    improved = aggregate.get("improved_count", 0)
    newly_reachable = aggregate.get("newly_reachable_count", 0)
    savings = aggregate.get("total_distance_savings_m", 0)
    numeric_values = (improved, newly_reachable, savings)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in numeric_values):
        return True
    has_shared_sample_benefit = improved > 0 or newly_reachable > 0 or savings > 0
    if has_shared_sample_benefit and _NO_IMPACT_TEXT.search(narrative):
        return True
    if not has_shared_sample_benefit and _POSITIVE_IMPACT_TEXT.search(narrative):
        return True
    return False


def validate_ai_planning_response(response: Any, packet: Mapping[str, Any]) -> dict[str, Any]:
    """Validate model references and attach authoritative SIM solution records."""
    if isinstance(response, str):
        if len(response.encode("utf-8")) > MAX_AI_RESPONSE_BYTES:
            return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("response_too_large")], "identified_problems": [], "recommended_solutions": []}
        try:
            response = json.loads(response, parse_constant=_parse_constant)
        except (json.JSONDecodeError, ValueError):
            return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("malformed_or_nonfinite_json")], "identified_problems": [], "recommended_solutions": []}
    try:
        packet_size = len(_canonical(packet).encode("utf-8"))
        expected_digest = _packet_digest(packet)
    except (TypeError, ValueError):
        packet_size, expected_digest = MAX_AI_PACKET_BYTES + 1, ""
    if packet_size > MAX_AI_PACKET_BYTES or packet.get("schema_version") != AI_PACKET_SCHEMA or not isinstance(packet.get("integrity"), Mapping) or packet["integrity"].get("sha256") != expected_digest or packet["integrity"].get("serialized_bytes") != packet_size:
        return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("invalid_or_corrupted_evidence_packet")], "identified_problems": [], "recommended_solutions": []}
    if not isinstance(response, Mapping):
        return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("response_not_object")], "identified_problems": [], "recommended_solutions": []}
    if set(response) != _TOP_FIELDS:
        return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("invalid_top_level_schema")], "identified_problems": [], "recommended_solutions": []}
    area_id = packet.get("study_area", {}).get("area_id") if isinstance(packet.get("study_area"), Mapping) else None
    base_area_id = packet.get("sim_proposal_context", {}).get("study_area", {}).get("area_id") if isinstance(packet.get("sim_proposal_context"), Mapping) and isinstance(packet["sim_proposal_context"].get("study_area"), Mapping) else None
    urban_area_id = packet.get("urban_intelligence", {}).get("area_id") if isinstance(packet.get("urban_intelligence"), Mapping) else None
    source_area_hash = packet.get("source", {}).get("area_geometry_sha256") if isinstance(packet.get("source"), Mapping) else None
    urban_area_hash = packet.get("urban_intelligence", {}).get("area_geometry_sha256") if isinstance(packet.get("urban_intelligence"), Mapping) else None
    if not isinstance(area_id, str) or base_area_id != area_id or urban_area_id != area_id or source_area_hash != urban_area_hash:
        return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("inconsistent_or_stale_evidence_area")], "identified_problems": [], "recommended_solutions": []}
    if response.get("schema_version") != AI_RESPONSE_SCHEMA or response.get("area_id") != area_id or response.get("evidence_packet_sha256") != expected_digest:
        return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("wrong_area_or_stale_packet")], "identified_problems": [], "recommended_solutions": []}
    try:
        serialized = _canonical(response)
    except (TypeError, ValueError):
        return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("response_not_finite_json")], "identified_problems": [], "recommended_solutions": []}
    if len(serialized.encode("utf-8")) > MAX_AI_RESPONSE_BYTES:
        return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("response_too_large")], "identified_problems": [], "recommended_solutions": []}
    if not isinstance(response.get("limitations"), list) or len(response["limitations"]) > 12 or any(not isinstance(item, str) or len(item) > 500 for item in response["limitations"]):
        return {"schema_version": "arteria.ai-planning-validation.v1", "status": "rejected", "findings": [_reject("invalid_limitations_array")], "identified_problems": [], "recommended_solutions": []}

    urban = packet.get("urban_intelligence", {})
    plan = packet.get("solution_plan", {})
    problems = [item for item in urban.get("problems", []) if isinstance(item, Mapping)] if isinstance(urban, Mapping) and isinstance(urban.get("problems"), list) else []
    solutions = [item for item in plan.get("solutions", []) if isinstance(item, Mapping)] if isinstance(plan, Mapping) and isinstance(plan.get("solutions"), list) else []
    problem_by_id = {str(item.get("problem_id")): item for item in problems if item.get("problem_id")}
    solution_by_id = {str(item.get("solution_id")): item for item in solutions if item.get("solution_id")}
    candidate_by_id = {str(item.get("candidate_id")): item for item in solutions if item.get("candidate_id")}
    proposal_context = packet.get("sim_proposal_context", {})
    evaluation_context = proposal_context.get("candidate_evaluation", {}) if isinstance(proposal_context, Mapping) else {}
    candidate_evidence_by_id = {
        str(item.get("candidate_id")): item
        for item in evaluation_context.get("candidates", [])
        if isinstance(item, Mapping) and item.get("candidate_id")
    } if isinstance(evaluation_context, Mapping) and isinstance(evaluation_context.get("candidates"), list) else {}
    known_evidence = set()
    for problem in problems:
        for evidence in problem.get("evidence", []) if isinstance(problem.get("evidence"), list) else []:
            if isinstance(evidence, Mapping) and isinstance(evidence.get("evidence_id"), str):
                known_evidence.add(evidence["evidence_id"])
    for gap in urban.get("coverage_gaps", []) if isinstance(urban, Mapping) and isinstance(urban.get("coverage_gaps"), list) else []:
        if isinstance(gap, Mapping) and isinstance(gap.get("gap_id"), str):
            known_evidence.add(gap["gap_id"])
    for observation in urban.get("simulation_observations", []) if isinstance(urban, Mapping) and isinstance(urban.get("simulation_observations"), list) else []:
        if isinstance(observation, Mapping) and isinstance(observation.get("observation_id"), str):
            known_evidence.add(observation["observation_id"])

    findings: list[dict[str, Any]] = []
    safe_problems = []
    seen_problems = set()
    raw_problems = response.get("identified_problems")
    if not isinstance(raw_problems, list) or len(raw_problems) > MAX_AI_PROBLEMS:
        findings.append(_reject("invalid_identified_problems_array"))
        raw_problems = []
    for index, item in enumerate(raw_problems):
        reason = None
        if not isinstance(item, Mapping) or set(item) != _PROBLEM_FIELDS:
            reason = "invalid_problem_entry_schema"
        else:
            problem_id = item.get("problem_id")
            evidence_ids = item.get("evidence_ids")
            if not isinstance(problem_id, str) or problem_id not in problem_by_id:
                reason = "unknown_problem_id"
            elif len(problem_id) > 100 or not _string_list(evidence_ids, maximum_items=8, maximum_length=120, nonempty=True):
                reason = "invalid_problem_entry_schema"
            elif problem_id in seen_problems:
                reason = "duplicate_problem_id"
            elif not set(evidence_ids).issubset({record.get("evidence_id") for record in problem_by_id[problem_id].get("evidence", []) if isinstance(record, Mapping)}):
                reason = "unknown_or_unrelated_evidence_id"
            elif _text_findings(item.get("explanation"), maximum=700):
                reason = _text_findings(item.get("explanation"), maximum=700)[0]
        if reason:
            findings.append(_reject(reason, index))
            continue
        seen_problems.add(problem_id)
        safe_problems.append({"problem_id": problem_id, "explanation": item["explanation"], "evidence_ids": sorted(set(evidence_ids))})

    safe_solutions = []
    seen_solutions = set()
    raw_solutions = response.get("recommended_solutions")
    if not isinstance(raw_solutions, list) or len(raw_solutions) > MAX_AI_SOLUTIONS:
        findings.append(_reject("invalid_recommended_solutions_array"))
        raw_solutions = []
    for index, item in enumerate(raw_solutions):
        reason = None
        if not isinstance(item, Mapping):
            reason = "invalid_solution_entry_schema"
        else:
            extra = set(item) - _SOLUTION_FIELDS
            missing = _SOLUTION_FIELDS - set(item)
            if missing or extra:
                if extra & {"geometry", "coordinates", "metrics", "impact", "cost", "citations", "source_citations", "sumo_run_id", "simulation_run_id", "run_id", "action_type", "intervention", "physical_feasibility", "buildability", "observed_metrics", "observations"}:
                    reason = "forbidden_authoritative_claim_or_action"
                else:
                    reason = "invalid_solution_entry_schema"
            elif not isinstance(item.get("solution_id"), str) or len(item.get("solution_id")) > 100 or item.get("solution_id") not in solution_by_id:
                reason = "unknown_solution_id"
            elif item.get("solution_id") in seen_solutions:
                reason = "duplicate_solution_id"
            else:
                authoritative = solution_by_id[item["solution_id"]]
                candidate_id = item.get("candidate_id")
                expected_candidate_id = authoritative.get("candidate_id")
                if candidate_id is not None and (not isinstance(candidate_id, str) or len(candidate_id) > 120):
                    reason = "invalid_solution_entry_schema"
                elif not isinstance(item.get("title"), str) or len(item["title"]) > 180 or not isinstance(item.get("expected_benefit_type"), str) or len(item["expected_benefit_type"]) > 100 or not _string_list(item.get("problem_ids"), maximum_items=8, maximum_length=100) or not _string_list(item.get("evidence_ids"), maximum_items=8, maximum_length=120, nonempty=True):
                    reason = "invalid_solution_entry_schema"
                elif candidate_id != expected_candidate_id:
                    reason = "unknown_or_mismatched_candidate_id"
                elif not set(item["problem_ids"]).issubset(set(authoritative.get("problem_ids", []))):
                    reason = "unknown_or_unrelated_problem_id"
                elif not set(item["evidence_ids"]).issubset(set(authoritative.get("evidence_ids", []))):
                    reason = "unknown_or_unrelated_evidence_id"
                elif item.get("expected_benefit_type") != authoritative.get("expected_benefit_type"):
                    reason = "contradictory_benefit_type"
                elif item.get("field_verification_required") is not True:
                    reason = "field_verification_required"
                elif _text_findings(item.get("title"), maximum=180) or _text_findings(item.get("explanation"), maximum=700):
                    combined = _text_findings(item.get("title"), maximum=180) + _text_findings(item.get("explanation"), maximum=700)
                    reason = combined[0]
                elif expected_candidate_id and authoritative.get("status") not in {"supported_evaluated", "supported_not_yet_evaluated"}:
                    reason = "candidate_not_authoritatively_supported"
                elif not expected_candidate_id and authoritative.get("status") != "concept_only_not_evaluated":
                    reason = "concept_status_mismatch"
                elif expected_candidate_id and _candidate_impact_contradiction(item, candidate_evidence_by_id.get(str(expected_candidate_id))):
                    reason = "contradictory_candidate_impact_claim"
        if reason:
            findings.append(_reject(reason, index))
            continue
        seen_solutions.add(item["solution_id"])
        authoritative_candidate = candidate_evidence_by_id.get(item["candidate_id"]) if item.get("candidate_id") else None
        authoritative_solution = dict(authoritative)
        if authoritative_candidate is not None:
            authoritative_solution.update({
                "geometry": authoritative_candidate.get("geometry"),
                "intervention": authoritative_candidate.get("intervention"),
                "shared_sample_impact": authoritative_candidate.get("shared_sample_impact"),
                "targeted_diagnostic_impact": authoritative_candidate.get("targeted_diagnostic_impact"),
                "screening": authoritative_candidate.get("screening"),
                "authoritative_candidate_evidence": authoritative_candidate,
            })
        safe_solutions.append({
            "solution_id": item["solution_id"],
            "candidate_id": item["candidate_id"],
            "problem_ids": sorted(set(item["problem_ids"])),
            "title": item["title"],
            "explanation": item["explanation"],
            "expected_benefit_type": item["expected_benefit_type"],
            "evidence_ids": sorted(set(item["evidence_ids"])),
            "field_verification_required": True,
            "authoritative_sim_solution": authoritative_solution,
        })

    raw_candidate_ids = response.get("supported_candidate_ids")
    if not _string_list(raw_candidate_ids, maximum_items=8, maximum_length=120):
        findings.append(_reject("invalid_supported_candidate_ids"))
    else:
        candidates_mentioned = {item["candidate_id"] for item in safe_solutions if item.get("candidate_id")}
        for candidate_id in raw_candidate_ids:
            if not isinstance(candidate_id, str) or candidate_id not in candidate_by_id:
                findings.append(_reject("unknown_candidate_id"))
            elif candidate_id not in candidates_mentioned:
                findings.append(_reject("unreferenced_candidate_id"))
        for candidate_id in sorted(candidates_mentioned - set(raw_candidate_ids)):
            findings.append(_reject("missing_supported_candidate_reference"))

    refs = response.get("evidence_references")
    if not _string_list(refs, maximum_items=96, maximum_length=120) or any(value not in known_evidence for value in refs):
        findings.append(_reject("unknown_evidence_reference"))
        refs = []
    required_refs = {value for item in safe_problems + safe_solutions for value in item.get("evidence_ids", [])}
    if not required_refs.issubset(set(refs)):
        findings.append(_reject("missing_top_level_evidence_reference"))
    if len(refs) != len(set(refs)):
        findings.append(_reject("duplicate_top_level_evidence_reference"))
    if response.get("requires_field_verification") is not True:
        findings.append(_reject("field_verification_required"))
    limitation_texts = response.get("limitations", []) if isinstance(response.get("limitations"), list) else []
    for text in [response.get("summary"), *limitation_texts]:
        text_findings = _text_findings(text, maximum=1200 if text == response.get("summary") else 500)
        for reason in text_findings:
            findings.append(_reject(reason))

    status = "completed_with_rejections" if findings else "validated"
    return {
        "schema_version": "arteria.ai-planning-validation.v1",
        "status": status,
        "area_id": area_id,
        "evidence_packet_sha256": expected_digest,
        "summary": response.get("summary") if isinstance(response.get("summary"), str) else "",
        "identified_problems": safe_problems,
        "recommended_solutions": safe_solutions,
        "limitations": [value for value in response.get("limitations", []) if isinstance(value, str)] if isinstance(response.get("limitations"), list) else [],
        "requires_field_verification": True,
        "findings": findings,
        "rejected_entry_count": sum(1 for item in findings if item.get("item_index") is not None),
    }


def run_ai_planning(
    packet: Mapping[str, Any],
    call_model: Callable[..., Any] | None,
    *,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Call an injected backend provider safely, then validate its response."""
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(float(timeout_seconds)) or not 0 < float(timeout_seconds) <= 120:
        raise ValueError("timeout_seconds must be finite and greater than zero, up to 120 seconds.")
    if call_model is None:
        return {"status": "provider_unavailable", "ai_generated": False, "provider_called": False, "validation": None, "error_code": "no_model_provider_configured"}
    try:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="arteria-ai-planning")
        future = executor.submit(
            call_model,
            packet=packet,
            system_prompt=AI_SYSTEM_PROMPT,
            output_schema=AI_OUTPUT_SCHEMA,
            timeout_seconds=float(timeout_seconds),
        )
        try:
            response = future.result(timeout=float(timeout_seconds))
        except concurrent.futures.TimeoutError:
            future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            return {"status": "timeout", "ai_generated": False, "provider_called": True, "validation": None, "error_code": "model_call_timeout"}
        finally:
            if future.done():
                executor.shutdown(wait=True, cancel_futures=True)
    except Exception as error:
        return {"status": "provider_error", "ai_generated": False, "provider_called": True, "validation": None, "error_code": type(error).__name__}
    validation = validate_ai_planning_response(response, packet)
    return {
        "status": "completed" if validation["status"] == "validated" else "completed_with_rejections" if validation["identified_problems"] or validation["recommended_solutions"] else "invalid_response",
        "ai_generated": True,
        "provider_called": True,
        "validation": validation,
        "error_code": None,
    }
