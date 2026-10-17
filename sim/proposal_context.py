"""Build a compact, deterministic evidence packet for a future planning model."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

from shapely.geometry import mapping

from .geo import OSMData
from .proposal_catalog import get_intervention_catalog


DEFAULT_MAX_PACKET_BYTES = 65_536
_DEFAULT_LIMITS = {"issues": 24, "indicators": 64, "candidates": 8, "rejected_candidates": 12, "route_samples": 8, "evidence_items": 12}


def _text(value: Any, limit: int = 2_000) -> str | None:
    if value is None:
        return None
    result = str(value)
    return result if len(result) <= limit else result[: limit - 1] + "…"


def _json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")))


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _stable_items(values: Any, key: str, limit: int) -> list[dict[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    items = [dict(value) for value in values if isinstance(value, Mapping)]
    items.sort(key=lambda item: str(item.get(key, "")))
    return items[:limit]


def _compact_issue(issue: Mapping[str, Any], evidence_limit: int) -> dict[str, Any]:
    output = {
        "id": _text(issue.get("id"), 200),
        "type": _text(issue.get("type"), 120),
        "severity": _text(issue.get("severity"), 40),
        "description": _text(issue.get("description")),
        "geometry": _json_copy(issue.get("geometry")) if issue.get("geometry") is not None else None,
        "metrics": _json_copy(issue.get("metrics", {})),
        "evidence": [],
        "data_coverage": _json_copy(issue.get("data_coverage", {})),
        "provenance": _json_copy(issue.get("provenance", [])),
        "uncertainty": _json_copy(issue.get("uncertainty", {})),
    }
    evidence = issue.get("evidence", [])
    if isinstance(evidence, Sequence) and not isinstance(evidence, (str, bytes)):
        for record in evidence[:evidence_limit]:
            if not isinstance(record, Mapping):
                continue
            compact = {}
            omitted = {}
            for name, value in record.items():
                if isinstance(value, list) and len(value) > evidence_limit:
                    compact[name] = _json_copy(value[:evidence_limit])
                    omitted[name] = len(value) - evidence_limit
                else:
                    compact[name] = _json_copy(value)
            if omitted:
                compact["omitted_evidence_item_count"] = omitted
            output["evidence"].append(compact)
    output["omitted_evidence_record_count"] = max(0, len(evidence) - evidence_limit) if isinstance(evidence, list) else 0
    return output


def _compact_route(route: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "origin_node_id": _text(route.get("origin_node_id"), 120),
        "destination_node_id": _text(route.get("destination_node_id"), 120),
        "outcome": _text(route.get("outcome"), 80),
    }
    for phase in ("before", "after"):
        item = route.get(phase)
        if not isinstance(item, Mapping):
            result[phase] = None
            continue
        result[phase] = {
            name: _json_copy(item.get(name))
            for name in ("status", "distance_m", "estimated_walk_time_s", "geometry_included")
            if name in item
        }
    return result


def _compact_impact(impact: Any, route_limit: int) -> dict[str, Any] | None:
    if not isinstance(impact, Mapping):
        return None
    routes = impact.get("routes", [])
    route_items = routes if isinstance(routes, list) else []
    return {
        "impact_id": _text(impact.get("impact_id"), 100),
        "method_version": _text(impact.get("method_version"), 100),
        "aggregate": _json_copy(impact.get("aggregate", {})),
        "sample": _json_copy(impact.get("sample", {})),
        "provenance": _json_copy(impact.get("provenance", {})),
        "routes": [_compact_route(route) for route in route_items[:route_limit] if isinstance(route, Mapping)],
        "omitted_route_count": max(0, len(route_items) - route_limit),
        "assumptions": [_text(value, 500) for value in impact.get("assumptions", [])[:12]] if isinstance(impact.get("assumptions"), list) else [],
        "warnings": [_text(value, 500) for value in impact.get("warnings", [])[:12]] if isinstance(impact.get("warnings"), list) else [],
    }


def _compact_candidate(candidate: Mapping[str, Any], route_limit: int) -> dict[str, Any]:
    screening = _mapping(candidate.get("screening"))
    mapped_layers = {}
    for layer_name in ("mapped_buildings", "mapped_water_or_barriers"):
        layer = _mapping(screening.get(layer_name))
        mapped_layers[layer_name] = {
            key: _json_copy(layer[key])
            for key in ("status", "classification", "intersection_count", "reason")
            if key in layer
        }
    return {
        "candidate_id": _text(candidate.get("candidate_id"), 160),
        "rank": _json_copy(candidate.get("rank")),
        "related_issue_ids": sorted(str(value) for value in candidate.get("related_issue_ids", []) if value is not None) if isinstance(candidate.get("related_issue_ids"), list) else [],
        "discovery": _json_copy(candidate.get("discovery", {})),
        "geometry": _json_copy(candidate.get("geometry")),
        "length_m": _json_copy(candidate.get("length_m")),
        "intervention": _json_copy(candidate.get("intervention", {})),
        "screening": {
            "status": _text(screening.get("status"), 100),
            "physical_feasibility": _text(screening.get("physical_feasibility"), 40) or "unknown",
            "recommendation_status": _text(screening.get("recommendation_status"), 100),
            "mapped_obstacles": mapped_layers,
            "missing_evidence": _json_copy(screening.get("missing_evidence", [])),
            "warnings": _json_copy(screening.get("warnings", [])),
        },
        "ranking_metrics": _json_copy(candidate.get("ranking_metrics", {})),
        "ranking_explanation": _text(candidate.get("ranking_explanation")),
        "selection_rationale": _text(candidate.get("selection_rationale")),
        "shared_sample_impact": _compact_impact(candidate.get("impact"), route_limit),
        "targeted_diagnostic_impact": _compact_impact(candidate.get("targeted_diagnostic_impact"), route_limit),
        "provenance": _json_copy(candidate.get("provenance", [])),
        "assumptions": _json_copy(candidate.get("assumptions", [])),
    }


def _compact_rejected(candidate: Mapping[str, Any]) -> dict[str, Any]:
    screening = _mapping(candidate.get("screening"))
    return {
        "candidate_id": _text(candidate.get("candidate_id"), 160),
        "geometry": _json_copy(candidate.get("geometry")),
        "length_m": _json_copy(candidate.get("length_m")),
        "status": _text(screening.get("status"), 100),
        "physical_feasibility": _text(screening.get("physical_feasibility"), 40) or "unknown",
        "exclusion_reasons": _json_copy(screening.get("exclusion_reasons", [])),
        "mapped_building_classification": _text(_mapping(screening.get("mapped_buildings")).get("classification"), 100),
        "executable": False,
    }


def _bounded_availability(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    output = {}
    for key in sorted(value, key=str):
        entry = value[key]
        if isinstance(entry, Mapping):
            output[str(key)] = {name: _json_copy(entry[name]) for name in ("status", "feature_count", "node_count", "edge_count", "coverage") if name in entry}
        else:
            output[str(key)] = _json_copy(entry)
    return output


def build_proposal_context(
    data: OSMData,
    analysis: Mapping[str, Any],
    candidate_evaluation: Mapping[str, Any],
    *,
    max_packet_bytes: int = DEFAULT_MAX_PACKET_BYTES,
    max_issues: int = _DEFAULT_LIMITS["issues"],
    max_indicators: int = _DEFAULT_LIMITS["indicators"],
    max_candidates: int = _DEFAULT_LIMITS["candidates"],
    max_rejected_candidates: int = _DEFAULT_LIMITS["rejected_candidates"],
    max_route_samples: int = _DEFAULT_LIMITS["route_samples"],
    max_evidence_items: int = _DEFAULT_LIMITS["evidence_items"],
) -> dict[str, Any]:
    """Create bounded model context from one matching analysis and evaluation."""
    limits = (max_packet_bytes, max_issues, max_indicators, max_candidates, max_rejected_candidates, max_route_samples, max_evidence_items)
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in limits):
        raise ValueError("Packet byte and item limits must be non-negative integers.")
    if max_packet_bytes < 1_024:
        raise ValueError("max_packet_bytes must be at least 1024 bytes.")

    area = _mapping(analysis.get("area"))
    area_id = str(data.area.area_id)
    if area.get("area_id") != area_id or candidate_evaluation.get("area_id") != area_id:
        raise ValueError("Analysis, candidate evaluation, and OSMData must refer to the same study area.")

    source_geometry = mapping(data.area.polygon)
    geometry_payload = json.dumps(source_geometry, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    geometry_sha256 = hashlib.sha256(geometry_payload.encode("utf-8")).hexdigest()
    provenance = _mapping(analysis.get("provenance"))
    evaluation_ranked = candidate_evaluation.get("ranked_candidates", [])
    evaluation_rejected = candidate_evaluation.get("rejected_candidates", [])
    ranked = _stable_items(evaluation_ranked, "candidate_id", len(evaluation_ranked) if isinstance(evaluation_ranked, list) else 0)
    rejected = _stable_items(evaluation_rejected, "candidate_id", len(evaluation_rejected) if isinstance(evaluation_rejected, list) else 0)
    ranked.sort(key=lambda item: (item.get("rank", math.inf), str(item.get("candidate_id", ""))))
    issues = _stable_items(analysis.get("issues", []), "id", len(analysis.get("issues", [])) if isinstance(analysis.get("issues"), list) else 0)
    indicators = _stable_items(analysis.get("indicators", []), "id", len(analysis.get("indicators", [])) if isinstance(analysis.get("indicators"), list) else 0)
    catalog = get_intervention_catalog()

    current = {"issues": max_issues, "indicators": max_indicators, "candidates": max_candidates, "rejected_candidates": max_rejected_candidates, "route_samples": max_route_samples, "evidence_items": max_evidence_items}
    while True:
        packet = {
            "schema_version": "arteria.proposal-context.v1",
            "study_area": {
                "city_id": str(data.area.city_id),
                "area_id": area_id,
                "boundary_source": str(data.area.boundary_source),
                "geometry_reference": {"sha256": geometry_sha256, "geometry_type": data.area.polygon.geom_type, "crs": "EPSG:4326"},
                "extent_wgs84": _json_copy(data.area.extent),
                "working_crs": str(data.area.working_crs),
            },
            "geographic_source": {
                key: _json_copy(provenance[key])
                for key in ("source", "source_version", "retrieved_at", "working_crs", "source_area")
                if key in provenance
            },
            "analysis": {
                "network_metrics": _json_copy(analysis.get("network_metrics", {})),
                "indicators": [
                    {key: _json_copy(value) for key, value in indicator.items() if key in {"id", "label", "value", "unit", "status", "provenance", "uncertainty"}}
                    for indicator in indicators[:current["indicators"]]
                ],
                "omitted_indicator_count": max(0, len(indicators) - current["indicators"]),
                "issues": [_compact_issue(issue, current["evidence_items"]) for issue in issues[:current["issues"]]],
                "omitted_issue_count": max(0, len(issues) - current["issues"]),
                "data_availability": _bounded_availability(analysis.get("layer_availability", {})),
                "uncertainty": _json_copy(analysis.get("uncertainty", {})),
                "warnings": [_text(value, 700) for value in analysis.get("warnings", [])[:20]] if isinstance(analysis.get("warnings"), list) else [],
            },
            "candidate_evaluation": {
                "status": _text(candidate_evaluation.get("recommendation_status"), 200),
                "ranking_methodology": _text(candidate_evaluation.get("ranking_rule"), 1_500),
                "shared_sample": _json_copy(candidate_evaluation.get("sample", {})),
                "shared_sample_used_for_ranking": _json_copy(candidate_evaluation.get("ranking_metadata", {})),
                "candidates": [_compact_candidate(candidate, current["route_samples"]) for candidate in ranked[:current["candidates"]]],
                "omitted_evaluated_candidate_count": max(0, len(ranked) - current["candidates"]),
                "rejected_candidates": [_compact_rejected(candidate) for candidate in rejected[:current["rejected_candidates"]]],
                "omitted_rejected_candidate_count": max(0, len(rejected) - current["rejected_candidates"]),
            },
            "capabilities": {
                "intervention_catalog_version": catalog["version"],
                "supported_intervention_types": [item["type_id"] for item in catalog["supported_interventions"]],
                "unsupported_simulation_capabilities": ["real_area_sumo_network_conversion", "traffic_demand_calibration", "observed_traffic_metrics", "construction_feasibility"],
            },
            "model_limitations": [
                "Graph-node route samples are calculated network probes, not observed journeys or population demand.",
                "A hypothetical pedestrian connection is not verified for safety, accessibility, ownership, legal approval, or construction feasibility.",
                "OSM mapping and tagged feature coverage can be incomplete; missing or empty layers do not establish real-world absence.",
                "Targeted diagnostic routes are candidate-specific and are excluded from shared-sample ranking.",
                "No real-area SUMO traffic simulation or calibrated traffic measurement is currently available from this engine.",
            ],
            "truncation": {
                "packet_byte_limit": max_packet_bytes,
                "selected_limits": current,
                "serialized_bytes": 0,
            },
        }
        for _ in range(3):
            serialized = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
            packet_bytes = len(serialized.encode("utf-8"))
            if packet["truncation"]["serialized_bytes"] == packet_bytes:
                break
            packet["truncation"]["serialized_bytes"] = packet_bytes
        final_serialized = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        actual_packet_bytes = len(final_serialized.encode("utf-8"))
        packet["truncation"]["serialized_bytes"] = actual_packet_bytes
        if actual_packet_bytes <= max_packet_bytes:
            return packet
        reducible = ("route_samples", "evidence_items", "candidates", "rejected_candidates", "issues", "indicators")
        changed = False
        for key in reducible:
            if current[key] > 0:
                current[key] = current[key] // 2
                changed = True
                break
        if not changed:
            raise ValueError("Core proposal context exceeds max_packet_bytes even after bounded evidence was removed.")
