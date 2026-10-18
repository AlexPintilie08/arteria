"""Evidence-linked supported and conceptual urban planning options."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from .geo import OSMData
from .proposal_validation import validate_proposal_set
from .proposals import prepare_candidate_options


SOLUTION_PLAN_SCHEMA = "arteria.solution-plan.v1"
MAX_SOLUTION_RECORDS = 32

_CONCEPTS = {
    "pedestrian_disconnection": (
        "field_verification",
        "Verificarea pe teren a posibilei întreruperi",
        "Verificați traseele pietonale, accesul public și continuitatea dintre componentele mapate înainte de a stabili dacă este necesară o intervenție.",
    ),
    "excessive_pedestrian_detour": (
        "network_mapping_validation",
        "Verificarea ocolirii din rețeaua pietonală",
        "Verificați pe teren continuitatea traseului mapat și traversările disponibile; ocolirea calculată descrie numai graful OSM.",
    ),
    "excessive_detour_to_mapped_destination": (
        "destination_accessibility_review",
        "Evaluarea accesului către destinația mapată",
        "Verificați traseul pietonal și accesul public către destinațiile din categoria menționată în dovezi.",
    ),
    "weak_access_to_mapped_destination": (
        "accessibility_review",
        "Verificarea accesului pietonal la destinația mapată",
        "Confirmați localizarea destinațiilor și legăturile pietonale; numărul de noduri nu estimează accesul populației.",
    ),
}


def _stable_id(*parts: Any) -> str:
    raw = "\0".join(str(part) for part in parts).encode("utf-8")
    return "sol_" + hashlib.sha256(raw).hexdigest()[:20]


def _ranked_candidates(evaluation: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    values = evaluation.get("ranked_candidates", [])
    if not isinstance(values, list):
        return []
    return sorted(
        (value for value in values if isinstance(value, Mapping)),
        key=lambda item: (item.get("rank", float("inf")), str(item.get("candidate_id", ""))),
    )


def _problem_evidence_ids(problem: Mapping[str, Any]) -> list[str]:
    result = []
    for item in problem.get("evidence", []) if isinstance(problem.get("evidence"), list) else []:
        if isinstance(item, Mapping) and isinstance(item.get("evidence_id"), str):
            result.append(item["evidence_id"])
    return sorted(set(result))


def _associated_problems(candidate_id: str, candidate: Mapping[str, Any], problems: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    issue_ids = set()
    rationale = candidate.get("rationale", {})
    related = rationale.get("related_issue_ids", []) if isinstance(rationale, Mapping) else []
    if isinstance(related, list):
        issue_ids = {str(item) for item in related}
    result = []
    for problem in problems:
        evidence_issue_ids = {
            str(evidence.get("source_issue_id"))
            for evidence in problem.get("evidence", [])
            if isinstance(evidence, Mapping) and evidence.get("source_issue_id") is not None
        } if isinstance(problem.get("evidence"), list) else set()
        if candidate_id in problem.get("related_candidate_ids", []) or (issue_ids & evidence_issue_ids):
            result.append(problem)
    return result


def build_solution_plan(
    data: OSMData,
    analysis: Mapping[str, Any],
    urban_issues: Mapping[str, Any],
    candidate_evaluation: Mapping[str, Any],
    *,
    max_solutions: int = MAX_SOLUTION_RECORDS,
) -> dict[str, Any]:
    """Link detected problems to validated candidates and limited concepts.

    Candidate geometry and numerical impact are copied from SIM's authoritative
    evaluation output. Conceptual options contain no geometry or benefit metric.
    """
    if isinstance(max_solutions, bool) or not isinstance(max_solutions, int) or not 1 <= max_solutions <= MAX_SOLUTION_RECORDS:
        raise ValueError(f"max_solutions must be an integer from 1 through {MAX_SOLUTION_RECORDS}.")
    area_id = data.area.area_id
    if analysis.get("area", {}).get("area_id") != area_id or candidate_evaluation.get("area_id") != area_id or urban_issues.get("area_id") != area_id:
        raise ValueError("Analysis, urban issues, candidate evaluation, and OSMData must refer to the same area.")
    raw_problems = urban_issues.get("problems", [])
    if not isinstance(raw_problems, list):
        raise ValueError("urban_issues.problems must be an array.")
    problems = [item for item in raw_problems if isinstance(item, Mapping) and isinstance(item.get("problem_id"), str)]

    options = prepare_candidate_options(analysis, candidate_evaluation)
    validation = validate_proposal_set(options, data=data, candidate_evaluation=candidate_evaluation)
    validation_by_candidate = {
        result.get("candidate_id"): result
        for result in validation.get("results", [])
        if isinstance(result, Mapping)
    }
    candidates_by_id = {str(item.get("candidate_id")): item for item in _ranked_candidates(candidate_evaluation) if item.get("candidate_id")}
    solutions: list[dict[str, Any]] = []

    for option in options:
        candidate_id = option.get("candidate_id")
        if not isinstance(candidate_id, str) or candidate_id not in candidates_by_id:
            continue
        linked = _associated_problems(candidate_id, option, problems)
        if not linked:
            continue
        source_candidate = candidates_by_id[candidate_id]
        validation_result = validation_by_candidate.get(candidate_id, {})
        status = "supported_evaluated" if validation_result.get("status") == "candidate_backed_evaluated" else "rejected"
        shared_impact = source_candidate.get("impact")
        targeted_impact = source_candidate.get("targeted_diagnostic_impact")
        if status == "supported_evaluated" and not isinstance(shared_impact, Mapping):
            status = "supported_not_yet_evaluated"
        primary = linked[0]
        evidence_ids = sorted({identifier for problem in linked for identifier in _problem_evidence_ids(problem)})
        aggregate = shared_impact.get("aggregate", {}) if isinstance(shared_impact, Mapping) else {}
        shared_sample = shared_impact.get("sample", {}) if isinstance(shared_impact, Mapping) else {}
        targeted = targeted_impact.get("aggregate", {}) if isinstance(targeted_impact, Mapping) else None
        targeted_sample = targeted_impact.get("sample", {}) if isinstance(targeted_impact, Mapping) else None
        screening = source_candidate.get("screening", {})
        solutions.append({
            "solution_id": _stable_id(area_id, "candidate", candidate_id),
            "status": status,
            "solution_type": "supported_candidate",
            "title": "Evaluarea conexiunii pietonale candidate",
            "description": "SIM a evaluat această conexiune pietonală ipotetică pe graful cartografiat. Rezultatul nu stabilește că traseul este sigur, accesibil, autorizat sau construibil.",
            "problem_ids": [item["problem_id"] for item in linked],
            "primary_problem_id": primary["problem_id"],
            "candidate_id": candidate_id,
            "action_type": source_candidate.get("intervention", {}).get("type") if isinstance(source_candidate.get("intervention"), Mapping) else None,
            "geometry": source_candidate.get("geometry") if status in {"supported_evaluated", "supported_not_yet_evaluated"} else None,
            "intervention": dict(source_candidate.get("intervention", {})) if status in {"supported_evaluated", "supported_not_yet_evaluated"} and isinstance(source_candidate.get("intervention"), Mapping) else None,
            "rationale": "Intervenția este legată de dovezile problemei detectate și păstrează rezultatul calculat de SIM.",
            "expected_benefit_type": "graph_connectivity_or_sampled_route_access",
            "shared_sample_impact": {"aggregate": aggregate, "sample": shared_sample, "used_for_ranking": True} if status == "supported_evaluated" else None,
            "targeted_diagnostic_impact": {"aggregate": targeted, "sample": targeted_sample, "used_for_ranking": False} if status == "supported_evaluated" and isinstance(targeted_impact, Mapping) else None,
            "screening": dict(screening) if isinstance(screening, Mapping) else {},
            "physical_feasibility": "unknown",
            "field_verification_required": True,
            "evidence_ids": evidence_ids,
            "validation": validation_result,
            "limitations": [
                "Graful și eșantionul de trasee sunt calculate din date mapate, nu din deplasări observate.",
                "Diagnosticul local specific candidatului nu influențează clasamentul pe eșantionul comun.",
                "Siguranța, accesibilitatea, proprietatea, aprobările și fezabilitatea construcției rămân neverificate.",
            ],
        })

    for problem in problems:
        concept = _CONCEPTS.get(str(problem.get("problem_type")))
        if concept is None:
            continue
        concept_type, title, rationale = concept
        evidence_ids = _problem_evidence_ids(problem)
        if not evidence_ids:
            continue
        solutions.append({
            "solution_id": _stable_id(area_id, "concept", problem["problem_id"], concept_type),
            "status": "concept_only_not_evaluated",
            "solution_type": concept_type,
            "title": title,
            "description": rationale,
            "problem_ids": [problem["problem_id"]],
            "primary_problem_id": problem["problem_id"],
            "candidate_id": None,
            "action_type": None,
            "geometry": None,
            "intervention": None,
            "rationale": "Idee de verificare bazată pe dovezile citate; SIM nu a modelat această acțiune.",
            "expected_benefit_type": "evidence_quality_or_field_review",
            "shared_sample_impact": None,
            "targeted_diagnostic_impact": None,
            "screening": None,
            "physical_feasibility": "unknown",
            "field_verification_required": True,
            "evidence_ids": evidence_ids,
            "limitations": ["Opțiune conceptuală; nu este intervenție executabilă și nu are impact numeric evaluat."],
        })

    for gap in urban_issues.get("coverage_gaps", []) if isinstance(urban_issues.get("coverage_gaps"), list) else []:
        if not isinstance(gap, Mapping) or not isinstance(gap.get("gap_id"), str):
            continue
        category = str(gap.get("category_id") or "")
        if category not in {"crossings", "schools", "healthcare", "public_transport", "services", "green_space"}:
            continue
        solutions.append({
            "solution_id": _stable_id(area_id, "coverage", gap["gap_id"]),
            "status": "concept_only_not_evaluated",
            "solution_type": "mapping_coverage_review",
            "title": f"Verificarea datelor mapate pentru categoria {category}",
            "description": "Verificați acoperirea OSM a categoriei; lipsa sau necunoașterea înregistrărilor mapate nu dovedește absența obiectelor în teren.",
            "problem_ids": [],
            "primary_problem_id": None,
            "candidate_id": None,
            "action_type": None,
            "geometry": None,
            "intervention": None,
            "rationale": "Propunere limitată la clarificarea acoperirii datelor.",
            "expected_benefit_type": "evidence_quality",
            "shared_sample_impact": None,
            "targeted_diagnostic_impact": None,
            "screening": None,
            "physical_feasibility": "unknown",
            "field_verification_required": True,
            "evidence_ids": [gap["gap_id"]],
            "limitations": ["Nu formulează o absență reală și nu presupune că o infrastructură nu există."],
        })

    solutions.sort(key=lambda item: (
        {"supported_evaluated": 0, "supported_not_yet_evaluated": 1, "concept_only_not_evaluated": 2, "unsupported": 3, "rejected": 4}.get(item["status"], 5),
        item.get("primary_problem_id") or "~",
        item.get("candidate_id") or item["solution_id"],
    ))
    solutions = solutions[:max_solutions]
    for solution in solutions:
        if solution["status"] in {"concept_only_not_evaluated", "unsupported", "rejected"} and (solution.get("geometry") or solution.get("intervention") or solution.get("shared_sample_impact")):
            raise ValueError("Conceptual, unsupported, and rejected solutions cannot expose executable geometry or impact claims.")
    status = "supported_candidates_available" if any(item["status"] in {"supported_evaluated", "supported_not_yet_evaluated"} for item in solutions) else "no_supported_solution"
    return {
        "schema_version": SOLUTION_PLAN_SCHEMA,
        "area_id": area_id,
        "status": status,
        "supported_action_types": sorted({item.get("action_type") for item in solutions if item.get("status") in {"supported_evaluated", "supported_not_yet_evaluated"} and item.get("action_type")}),
        "problem_count": len(problems),
        "candidate_validation": validation,
        "solutions": solutions,
        "simulation_observations": list(urban_issues.get("simulation_observations", [])) if isinstance(urban_issues.get("simulation_observations"), list) else [],
        "limitations": [
            "SIM candidate metrics describe graph calculations and only the shared sample is used for ranking.",
            "Conceptual options are not executable scenarios and have no modeled impact.",
            "No physical feasibility, safety, ownership, legal or construction conclusion is provided.",
            "SUMO output is reported separately as simulated output under synthetic demand, not measured traffic.",
        ],
    }
