"""Deterministic candidate-backed option preparation for downstream planners."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .proposal_catalog import INTERVENTION_CATALOG_VERSION


def prepare_candidate_options(
    analysis: Mapping[str, Any],
    candidate_evaluation: Mapping[str, Any],
    *,
    max_options: int = 8,
) -> list[dict[str, Any]]:
    """Return ranked, actually evaluated graph candidates without planning labels."""
    if isinstance(max_options, bool) or not isinstance(max_options, int) or max_options < 0:
        raise ValueError("max_options must be a non-negative integer.")
    analysis_area = analysis.get("area", {})
    area_id = analysis_area.get("area_id") if isinstance(analysis_area, Mapping) else None
    if area_id is None or candidate_evaluation.get("area_id") != area_id:
        raise ValueError("Analysis and candidate evaluation must refer to the same study area.")
    provenance = analysis.get("provenance", {})
    provenance = provenance if isinstance(provenance, Mapping) else {}
    source = str(provenance.get("source", "unknown"))
    source_version = str(provenance.get("source_version", "unknown"))
    source_area = provenance.get("source_area", {})
    cache = provenance.get("cache", {})
    if "fixture" in source.casefold() or "fixture" in source_version.casefold():
        source_area_verification = "synthetic_fixture"
    elif (isinstance(cache, Mapping) and cache.get("area_equivalence_verified") is False) or (isinstance(source_area, Mapping) and source_area.get("equivalence_verified") is False):
        source_area_verification = "unverified"
    elif source == "OpenStreetMap":
        source_area_verification = "verified"
    else:
        source_area_verification = "unknown"

    known_issue_ids = {
        str(issue.get("id"))
        for issue in analysis.get("issues", [])
        if isinstance(issue, Mapping) and issue.get("id") is not None
    } if isinstance(analysis.get("issues", []), list) else set()
    options = []
    candidates = candidate_evaluation.get("ranked_candidates", [])
    if not isinstance(candidates, list):
        return options
    ordered = sorted(
        (candidate for candidate in candidates if isinstance(candidate, Mapping)),
        key=lambda candidate: (candidate.get("rank", float("inf")), str(candidate.get("candidate_id", ""))),
    )
    for candidate in ordered:
        if len(options) >= max_options:
            break
        intervention = candidate.get("intervention")
        impact = candidate.get("impact")
        if not isinstance(intervention, Mapping) or intervention.get("type") != "add_pedestrian_connection":
            continue
        if not isinstance(impact, Mapping) or not isinstance(impact.get("aggregate"), Mapping):
            continue
        screening = candidate.get("screening", {})
        screening = screening if isinstance(screening, Mapping) else {}
        related_issue_ids = sorted(
            issue_id for issue_id in (str(value) for value in candidate.get("related_issue_ids", []))
            if issue_id in known_issue_ids
        )
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            continue
        warnings = screening.get("warnings", [])
        options.append({
            "candidate_id": candidate_id,
            "area_id": str(area_id),
            "data_source": source,
            "source_area_verification": source_area_verification,
            "rank": candidate.get("rank"),
            "planning_category": None,
            "planning_category_status": "unclassified",
            "planning_category_reason": "SIM has no validated mapping from graph-link length or impact to Minimală, Moderată, or Transformatoare engineering classes.",
            "summary": "Candidate-backed hypothetical pedestrian graph connection; field review is required.",
            "rationale": {
                "related_issue_ids": related_issue_ids,
                "discovery_method": (candidate.get("discovery") or {}).get("method") if isinstance(candidate.get("discovery"), Mapping) else None,
                "selection": candidate.get("selection_rationale"),
                "ranking": candidate.get("ranking_explanation"),
            },
            "geometry": candidate.get("geometry"),
            "intervention": dict(intervention),
            "modeled_impact": {
                "status": "calculated_graph_sample",
                "impact_id": impact.get("impact_id"),
                "aggregate": dict(impact["aggregate"]),
                "shared_sample": dict(impact.get("sample", {})),
                "targeted_diagnostic_sample": dict((candidate.get("targeted_diagnostic_impact") or {}).get("sample", {})) if isinstance(candidate.get("targeted_diagnostic_impact"), Mapping) else {},
                "observed": False,
            },
            "screening": {
                "status": screening.get("status"),
                "physical_feasibility": "unknown",
                "missing_evidence": list(screening.get("missing_evidence", [])) if isinstance(screening.get("missing_evidence", []), list) else [],
                "warnings": list(warnings) if isinstance(warnings, list) else [],
            },
            "construction_cost": {"status": "unsupported", "value": None, "unit": None},
            "intervention_catalog_version": INTERVENTION_CATALOG_VERSION,
            "evaluation_status": "candidate_evaluated_on_graph",
        })
    return options
