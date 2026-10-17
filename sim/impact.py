"""Deterministic multi-route evaluation for supported SIM interventions."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

import networkx as nx

from .analysis import _node_sort_key, _nodes_inside_area, project_graph, route_between
from .geo import OSMData, geojson_geometry
from .scenario import (
    WALK_SPEED_MPS,
    _prepare_scenario_graph,
    _route_geometry,
)


IMPACT_METHOD_VERSION = "arteria-multi-route-impact-v1"
DEFAULT_ROUTE_SAMPLE_COUNT = 32
MAX_ROUTE_SAMPLE_COUNT = 200
DEFAULT_ROUTE_GEOMETRY_LIMIT = 20
MAX_ROUTE_GEOMETRY_LIMIT = 100
MAX_ROUTE_PATH_NODE_IDS = 500


def _canonical_pair(origin: Any, destination: Any) -> tuple[tuple[str, str], tuple[str, str]]:
    return tuple(sorted((_node_sort_key(origin), _node_sort_key(destination))))


def _eligible_graph_nodes(data: OSMData) -> tuple[nx.Graph, list[Any]]:
    if "walk" not in data.graphs:
        raise ValueError("A walking baseline network is required for route sampling.")
    graph = project_graph(data.graphs["walk"], data.area.working_crs)
    area_nodes = _nodes_inside_area(graph, data.area)
    return graph, sorted(area_nodes, key=_node_sort_key)


def _parse_route_pair(pair: Any, index: int) -> tuple[Any, Any]:
    if isinstance(pair, Mapping):
        origin, destination = pair.get("origin"), pair.get("destination")
    elif isinstance(pair, (tuple, list)) and len(pair) == 2:
        origin, destination = pair
    else:
        raise ValueError(f"route_pairs[{index}] must be a two-node pair or an origin/destination mapping.")
    if origin is None or destination is None:
        raise ValueError(f"route_pairs[{index}] must identify both origin and destination nodes.")
    return origin, destination


def _select_route_pairs(
    graph: nx.Graph,
    eligible_nodes: list[Any],
    *,
    route_pairs: Iterable[Any] | None,
    sample_count: int,
    seed: str | int,
    exclude_pairs: Iterable[tuple[Any, Any]],
) -> list[tuple[Any, Any]]:
    if route_pairs is not None:
        result: list[tuple[Any, Any]] = []
        seen: set[tuple[tuple[str, str], tuple[str, str]]] = set()
        eligible = set(eligible_nodes)
        for index, raw_pair in enumerate(route_pairs):
            origin, destination = _parse_route_pair(raw_pair, index)
            if origin not in graph or destination not in graph:
                missing = [str(node) for node in (origin, destination) if node not in graph]
                raise ValueError(f"route_pairs[{index}] contains unknown walking graph node(s): {', '.join(missing)}.")
            if origin not in eligible or destination not in eligible:
                raise ValueError(f"route_pairs[{index}] endpoints must lie inside the selected study polygon.")
            if origin == destination:
                raise ValueError(f"route_pairs[{index}] endpoints must be different graph nodes.")
            key = _canonical_pair(origin, destination)
            if key not in seen:
                result.append((origin, destination))
                seen.add(key)
        if not result:
            raise ValueError("At least one valid route pair is required.")
        return result

    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or not (1 <= sample_count <= MAX_ROUTE_SAMPLE_COUNT):
        raise ValueError(f"sample_count must be an integer from 1 through {MAX_ROUTE_SAMPLE_COUNT}.")
    if not isinstance(seed, (str, int)) or isinstance(seed, bool):
        raise ValueError("seed must be a string or integer.")
    if len(eligible_nodes) < 2:
        return []
    excluded = {_canonical_pair(origin, destination) for origin, destination in exclude_pairs if origin != destination}
    stable_seed = str(seed)
    result = []
    seen = set(excluded)
    # A bounded deterministic hash sampler avoids materializing all O(n^2) pairs.
    attempt_limit = min(max(sample_count * max(32, len(eligible_nodes) * 8), sample_count), 200_000)
    for attempt in range(attempt_limit):
        origin_hash = hashlib.sha256(f"{stable_seed}|{attempt}|origin".encode("utf-8")).digest()
        destination_hash = hashlib.sha256(f"{stable_seed}|{attempt}|destination".encode("utf-8")).digest()
        origin = eligible_nodes[int.from_bytes(origin_hash[:8], "big") % len(eligible_nodes)]
        destination = eligible_nodes[int.from_bytes(destination_hash[:8], "big") % len(eligible_nodes)]
        if origin == destination:
            continue
        key = _canonical_pair(origin, destination)
        if key in seen:
            continue
        seen.add(key)
        result.append((origin, destination))
        if len(result) >= sample_count:
            break
    return result


def sample_route_pairs(
    data: OSMData,
    *,
    route_pairs: Iterable[Any] | None = None,
    sample_count: int = DEFAULT_ROUTE_SAMPLE_COUNT,
    seed: str | int = "arteria-v1",
    exclude_pairs: Iterable[tuple[Any, Any]] = (),
) -> list[tuple[Any, Any]]:
    """Return explicit or reproducibly hash-sampled in-area graph-node pairs.

    The seeded hash ordering is deterministic and does not use process-global
    randomness. Pair outputs describe analysis samples only, never observed
    trips or population demand.
    """
    graph, eligible_nodes = _eligible_graph_nodes(data)
    return _select_route_pairs(
        graph,
        eligible_nodes,
        route_pairs=route_pairs,
        sample_count=sample_count,
        seed=seed,
        exclude_pairs=exclude_pairs,
    )


def _outcome(before: Mapping[str, Any], after: Mapping[str, Any]) -> tuple[str, float | None]:
    before_status, after_status = before["status"], after["status"]
    if before_status == "reachable" and after_status == "reachable":
        delta = float(after["distance_m"]) - float(before["distance_m"])
        return ("improved" if delta < -0.01 else "regressed" if delta > 0.01 else "unchanged"), delta
    if before_status == "unreachable" and after_status == "reachable":
        return "newly_reachable", None
    if before_status == "reachable" and after_status == "unreachable":
        return "newly_unreachable", None
    return "unreachable_in_both", None


def _route_payload(
    graph: nx.Graph,
    route: Mapping[str, Any],
    *,
    include_geometry: bool,
    working_crs: str,
    walking_speed_mps: float,
) -> dict[str, Any]:
    status = route["status"]
    path = list(route["path"])
    distance = route["distance_m"]
    estimated_time = float(distance) / walking_speed_mps if distance is not None else None
    geometry = _route_geometry(graph, path) if include_geometry and status == "reachable" else None
    return {
        "status": status,
        "network_distance_m": distance,
        "direct_distance_m": route["direct_distance_m"],
        "detour_ratio": route["detour_ratio"],
        "estimated_walk_time_s": estimated_time,
        "path_node_ids": [str(node) for node in path[:MAX_ROUTE_PATH_NODE_IDS]],
        "path_node_count": len(path),
        "path_node_ids_truncated": len(path) > MAX_ROUTE_PATH_NODE_IDS,
        "geometry": geojson_geometry(geometry, working_crs) if geometry is not None else None,
        "geometry_included": geometry is not None,
    }


def evaluate_multi_route_impact(
    data: OSMData,
    interventions: Iterable[dict[str, Any]],
    *,
    route_pairs: Iterable[Any] | None = None,
    sample_count: int = DEFAULT_ROUTE_SAMPLE_COUNT,
    seed: str | int = "arteria-v1",
    exclude_pairs: Iterable[tuple[Any, Any]] = (),
    walking_speed_mps: float = WALK_SPEED_MPS,
    max_snap_distance_m: float = 50.0,
    route_geometry_limit: int = DEFAULT_ROUTE_GEOMETRY_LIMIT,
) -> dict[str, Any]:
    """Evaluate one alternative against a consistent set of graph-node routes.

    The existing scenario graph-editing routine creates a fresh baseline copy
    and applies the interventions once. All OD calculations use those same
    baseline/scenario graphs and explicit speed assumptions.
    """
    walking_speed_mps = _validate_impact_settings(walking_speed_mps, route_geometry_limit)
    excluded_pairs = list(exclude_pairs)
    baseline_graph, eligible_nodes = _eligible_graph_nodes(data)
    selected_pairs = _select_route_pairs(
        baseline_graph,
        eligible_nodes,
        route_pairs=route_pairs,
        sample_count=sample_count,
        seed=seed,
        exclude_pairs=excluded_pairs,
    )
    if not selected_pairs:
        raise ValueError("At least two eligible walking graph nodes are required to evaluate route impact.")
    return _evaluate_selected_pairs(
        data,
        interventions,
        selected_pairs,
        baseline_graph=baseline_graph,
        eligible_node_count=len(eligible_nodes),
        explicit_pairs=route_pairs is not None,
        requested_pair_count=None if route_pairs is not None else sample_count,
        seed=seed,
        excluded_pair_count=0 if route_pairs is not None else len(excluded_pairs),
        walking_speed_mps=walking_speed_mps,
        max_snap_distance_m=max_snap_distance_m,
        route_geometry_limit=route_geometry_limit,
    )


def _validate_impact_settings(walking_speed_mps: float, route_geometry_limit: int) -> float:
    try:
        walking_speed_mps = float(walking_speed_mps)
    except (TypeError, ValueError) as error:
        raise ValueError("walking_speed_mps must be finite and positive.") from error
    if not math.isfinite(walking_speed_mps) or walking_speed_mps <= 0:
        raise ValueError("walking_speed_mps must be finite and positive.")
    if isinstance(route_geometry_limit, bool) or not isinstance(route_geometry_limit, int) or not (0 <= route_geometry_limit <= MAX_ROUTE_GEOMETRY_LIMIT):
        raise ValueError(f"route_geometry_limit must be an integer from 0 through {MAX_ROUTE_GEOMETRY_LIMIT}.")
    return walking_speed_mps


def _evaluate_selected_pairs(
    data: OSMData,
    interventions: Iterable[dict[str, Any]],
    selected_pairs: list[tuple[Any, Any]],
    *,
    baseline_graph: nx.Graph,
    eligible_node_count: int,
    explicit_pairs: bool,
    requested_pair_count: int | None,
    seed: str | int,
    excluded_pair_count: int,
    walking_speed_mps: float,
    max_snap_distance_m: float,
    route_geometry_limit: int,
) -> dict[str, Any]:
    baseline_graph, scenario_graph, applied = _prepare_scenario_graph(
        data,
        interventions,
        max_snap_distance_m=max_snap_distance_m,
        walking_speed_mps=walking_speed_mps,
        baseline_graph=baseline_graph,
    )
    result_rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    comparable_savings: list[float] = []
    geometry_budget = route_geometry_limit
    for origin, destination in selected_pairs:
        before_route = route_between(baseline_graph, origin, destination)
        after_route = route_between(scenario_graph, origin, destination)
        outcome, distance_delta = _outcome(before_route, after_route)
        counts[outcome] += 1
        if distance_delta is not None:
            comparable_savings.append(-distance_delta)
        include_before_geometry = before_route["status"] == "reachable" and geometry_budget > 0
        geometry_budget -= int(include_before_geometry)
        include_after_geometry = after_route["status"] == "reachable" and geometry_budget > 0
        geometry_budget -= int(include_after_geometry)
        before = _route_payload(baseline_graph, before_route, include_geometry=include_before_geometry, working_crs=data.area.working_crs, walking_speed_mps=walking_speed_mps)
        after = _route_payload(scenario_graph, after_route, include_geometry=include_after_geometry, working_crs=data.area.working_crs, walking_speed_mps=walking_speed_mps)
        result_rows.append({
            "origin_node_id": str(origin),
            "destination_node_id": str(destination),
            "before": before,
            "after": after,
            "outcome": outcome,
            "distance_delta_m": distance_delta,
            "distance_savings_m": -distance_delta if distance_delta is not None else None,
            "time_delta_s": distance_delta / walking_speed_mps if distance_delta is not None else None,
            "time_savings_s": -distance_delta / walking_speed_mps if distance_delta is not None else None,
            "improvement_percent": None,
        })

    sample = {
        "kind": "explicit_origin_destination_pairs" if explicit_pairs else "deterministic_graph_node_pair_sample",
        "method": "explicit caller-supplied graph node IDs" if explicit_pairs else "SHA-256 hash ranking from the seed and stable graph node IDs; no global randomness or all-pairs materialization",
        "seed": None if explicit_pairs else str(seed),
        "requested_pair_count": requested_pair_count,
        "evaluated_pair_count": len(selected_pairs),
        "eligible_graph_node_count": eligible_node_count,
        "excluded_discovery_pairs": excluded_pair_count,
        "interpretation": "Sampled graph-node pairs are analytical probes, not observed journeys or population demand; no representativeness or resident totals are inferred.",
    }
    savings_total = float(sum(comparable_savings))
    savings_average = float(statistics.mean(comparable_savings)) if comparable_savings else None
    savings_median = float(statistics.median(comparable_savings)) if comparable_savings else None
    added_lines = [
        {key: value for key, value in item.items() if key != "geometry"}
        | ({"geometry": geojson_geometry(item["geometry"], data.area.working_crs)} if item.get("geometry") is not None else {})
        for item in applied
    ]
    identity_payload = {
        "method": IMPACT_METHOD_VERSION,
        "interventions": [
            {key: value for key, value in item.items() if key not in {"geometry", "estimated_walk_time_s"}}
            for item in added_lines
        ],
        "pairs": [[str(origin), str(destination)] for origin, destination in selected_pairs],
        "speed_mps": walking_speed_mps,
    }
    impact_id = "impact_" + hashlib.sha256(json.dumps(identity_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()[:20]
    comparable_count = len(comparable_savings)
    return {
        "schema_version": 1,
        "impact_id": impact_id,
        "method_version": IMPACT_METHOD_VERSION,
        "area_id": data.area.area_id,
        "mode": "walk",
        "interventions": added_lines,
        "sample": sample,
        "routes": result_rows,
        "aggregate": {
            "evaluated_pair_count": len(result_rows),
            "improved_count": counts["improved"],
            "unchanged_count": counts["unchanged"],
            "regressed_count": counts["regressed"],
            "newly_reachable_count": counts["newly_reachable"],
            "newly_unreachable_count": counts["newly_unreachable"],
            "unreachable_in_both_count": counts["unreachable_in_both"],
            "reachable_both_comparable_pair_count": comparable_count,
            "total_distance_savings_m": savings_total if comparable_count else None,
            "average_distance_savings_m": savings_average,
            "median_distance_savings_m": savings_median,
            "total_estimated_time_savings_s": savings_total / walking_speed_mps if comparable_count else None,
            "average_estimated_time_savings_s": savings_average / walking_speed_mps if savings_average is not None else None,
            "reachability_change_count": counts["newly_reachable"] + counts["newly_unreachable"],
            "improvement_percent": None,
        },
        "configuration": {
            "walking_speed_mps": walking_speed_mps,
            "max_snap_distance_m": float(max_snap_distance_m),
            "route_geometry_limit": route_geometry_limit,
            "route_geometries_included_count": sum(
                int(route["before"]["geometry_included"]) + int(route["after"]["geometry_included"])
                for route in result_rows
            ),
        },
        "provenance": {
            "source": data.metadata.get("source", "unknown"),
            "source_version": data.metadata.get("source_version", "unknown"),
            "retrieved_at": data.metadata.get("retrieved_at"),
            "working_crs": data.area.working_crs,
            "method": "NetworkX weighted shortest paths on one immutable baseline graph and one isolated scenario graph",
        },
        "assumptions": [
            "Each alternative starts from the same original walking graph; edits are never accumulated between alternatives.",
            f"Estimated walking time assumes a constant {walking_speed_mps:g} m/s speed.",
            "Only graph-node reachability and length-weighted paths are measured; crossings, slope, delays, demand, and physical feasibility are not modeled.",
        ],
        "warnings": [
            "OSM network coverage can be incomplete; an unreachable graph pair is not proof of real-world disconnection.",
            "Sampled routes are graph-node pairs, not observed trips or a statistically representative travel sample.",
            "Route geometries are independently capped; every selected pair is included in numerical aggregate calculations.",
        ],
    }


def evaluate_candidates(
    data: OSMData,
    *,
    analysis: Mapping[str, Any] | None = None,
    max_candidates: int = 3,
    sample_count: int = DEFAULT_ROUTE_SAMPLE_COUNT,
    seed: str | int = "arteria-v1",
    route_geometry_limit: int = DEFAULT_ROUTE_GEOMETRY_LIMIT,
    max_connection_length_m: float = 1_000.0,
    detour_ratio_threshold: float = 2.0,
) -> dict[str, Any]:
    """Discover, independently evaluate, explain, and rank graph candidates.

    Ranking is lexicographic: more newly reachable sampled pairs, then more
    improved pairs, then larger aggregate distance savings, then fewer mapped
    obstacle intersections, fewer unknown obstacle layers, shorter links, and
    stable candidate ID.
    This is a graph-screening order, not a project feasibility or cost score.
    """
    from .analysis import analyze_snapshot
    from .candidates import discover_intervention_candidates

    baseline_analysis = dict(analysis) if analysis is not None else analyze_snapshot(data)
    baseline_summary = {
        "analysis_id": baseline_analysis.get("analysis_id"),
        "area": baseline_analysis.get("area"),
        "issues": baseline_analysis.get("issues", []),
        "network_metrics": baseline_analysis.get("network_metrics", {}),
        "layer_availability": baseline_analysis.get("layer_availability", data.layer_availability),
        "provenance": baseline_analysis.get("provenance", data.metadata),
        "warnings": baseline_analysis.get("warnings", data.warnings),
    }
    discovery = discover_intervention_candidates(
        data,
        issues=baseline_analysis.get("issues", []),
        max_candidates=max_candidates,
        max_connection_length_m=max_connection_length_m,
        detour_ratio_threshold=detour_ratio_threshold,
    )
    candidates = discovery["candidates"]
    if not candidates:
        return {
            "schema_version": 1,
            "area_id": data.area.area_id,
            "analysis_id": baseline_analysis.get("analysis_id"),
            "baseline_analysis": baseline_summary,
            "ranking_rule": "No graph-valid candidate was discovered; no recommendation is returned.",
            "candidate_discovery": discovery,
            "sample": {"kind": "not_created", "reason": "There are no candidate alternatives to evaluate."},
            "ranked_candidates": [],
            "warnings": discovery.get("warnings", []),
        }

    baseline_graph, eligible_nodes = _eligible_graph_nodes(data)
    node_by_string = {str(node): node for node in baseline_graph.nodes}
    discovery_pairs = []
    for candidate in candidates:
        start_id = candidate["start"]["node_id"]
        end_id = candidate["end"]["node_id"]
        if start_id in node_by_string and end_id in node_by_string:
            discovery_pairs.append((node_by_string[start_id], node_by_string[end_id]))
    shared_pairs = _select_route_pairs(
        baseline_graph,
        eligible_nodes,
        route_pairs=None,
        sample_count=sample_count,
        seed=seed,
        exclude_pairs=discovery_pairs,
    )
    if not shared_pairs:
        return {
            "schema_version": 1,
            "area_id": data.area.area_id,
            "analysis_id": baseline_analysis.get("analysis_id"),
            "baseline_analysis": baseline_summary,
            "candidate_generation_method_version": discovery["method_version"],
            "ranking_rule": "No independent evaluation sample was available after excluding candidate discovery pairs; no ranking is returned.",
            "candidate_discovery": discovery["screening"],
            "sample": {"kind": "unavailable", "reason": "No in-area graph-node pair remained outside the discovery pairs."},
            "ranked_candidates": [],
            "warnings": ["Candidate discovery and evaluation routes are kept separate; the discovery pair was not reused to inflate impact."],
        }
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        impact = _evaluate_selected_pairs(
            data,
            [candidate["intervention"]],
            shared_pairs,
            baseline_graph=baseline_graph,
            eligible_node_count=len(eligible_nodes),
            explicit_pairs=False,
            requested_pair_count=sample_count,
            seed=seed,
            excluded_pair_count=len(discovery_pairs),
            walking_speed_mps=WALK_SPEED_MPS,
            max_snap_distance_m=50.0,
            route_geometry_limit=route_geometry_limit,
        )
        aggregate = impact["aggregate"]
        obstacle_count = int(candidate["screening"]["mapped_buildings"].get("intersection_count", 0)) + int(candidate["screening"]["mapped_water_or_barriers"].get("intersection_count", 0))
        unknown_obstacle_layers = sum(
            candidate["screening"][layer]["status"] == "unknown"
            for layer in ("mapped_buildings", "mapped_water_or_barriers")
        )
        total_savings = aggregate["total_distance_savings_m"]
        candidate["impact"] = impact
        candidate["evaluation_rationale"] = [
            f"Evaluated {aggregate['evaluated_pair_count']} sampled graph-node pairs against the shared baseline sample.",
            f"{aggregate['improved_count']} improved and {aggregate['newly_reachable_count']} became reachable; {aggregate['regressed_count']} regressed and {aggregate['newly_unreachable_count']} became unreachable.",
            "Impact metrics describe the sampled graph only and do not estimate residents or observed trips.",
        ]
        candidate["ranking_metrics"] = {
            "newly_reachable_pairs": aggregate["newly_reachable_count"],
            "improved_pairs": aggregate["improved_count"],
            "total_distance_savings_m": total_savings,
            "mapped_obstacle_intersections": obstacle_count,
            "unknown_obstacle_layer_count": unknown_obstacle_layers,
            "intervention_length_m": candidate["length_m"],
            "tie_breaker_candidate_id": candidate["candidate_id"],
        }
        candidate["ranking_explanation"] = "Lexicographic order: newly reachable pairs descending, improved pairs descending, comparable distance savings descending, mapped obstacle intersections ascending, unknown obstacle layers ascending, link length ascending, then stable candidate ID."
        ranked.append(candidate)

    ranked.sort(key=lambda item: (
        -item["ranking_metrics"]["newly_reachable_pairs"],
        -item["ranking_metrics"]["improved_pairs"],
        -round(item["ranking_metrics"]["total_distance_savings_m"] or 0.0, 6),
        item["ranking_metrics"]["mapped_obstacle_intersections"],
        item["ranking_metrics"]["unknown_obstacle_layer_count"],
        item["ranking_metrics"]["intervention_length_m"],
        item["candidate_id"],
    ))
    for rank, candidate in enumerate(ranked, start=1):
        candidate["rank"] = rank
    sample_meta = ranked[0]["impact"]["sample"]
    return {
        "schema_version": 1,
        "area_id": data.area.area_id,
        "analysis_id": baseline_analysis.get("analysis_id"),
        "baseline_analysis": baseline_summary,
        "candidate_generation_method_version": discovery["method_version"],
        "impact_method_version": IMPACT_METHOD_VERSION,
        "ranking_rule": "Lexicographic: newly reachable sampled pairs descending; improved pairs descending; total distance savings among pairs reachable both before and after descending; mapped obstacle intersections ascending; unknown obstacle layers ascending; hypothetical link length ascending; stable candidate ID ascending.",
        "candidate_discovery": discovery["screening"],
        "sample": sample_meta,
        "ranked_candidates": ranked,
        "warnings": [
            *data.warnings,
            "All alternatives were evaluated independently from the same original baseline graph.",
            "The ranking is a graph-only comparison over sampled graph-node pairs; it is not a construction recommendation, feasibility score, or population impact estimate.",
            "Candidate and route geometry do not establish safety, ownership, legal approval, or buildability.",
        ],
    }
