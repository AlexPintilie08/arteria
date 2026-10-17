"""Bounded, deterministic discovery of hypothetical pedestrian links."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from typing import Any, Iterable, Mapping

import geopandas as gpd
import networkx as nx
from pyproj import CRS
from shapely import STRtree
from shapely.geometry import LineString, Point, shape

from .analysis import _node_sort_key, project_graph
from .geo import OSMData, geojson_geometry
from .scenario import MAX_CONNECTION_LENGTH_M


CANDIDATE_METHOD_VERSION = "arteria-pedestrian-candidates-v1"
DEFAULT_CANDIDATE_LIMIT = 3
DEFAULT_MAX_SCREENED_PAIRS = 10_000
DEFAULT_MAX_SOURCE_NODES = 500
DEFAULT_NEIGHBORS_PER_SOURCE = 20
DEFAULT_DETOUR_RATIO_THRESHOLD = 2.0


def _components(graph: nx.Graph) -> tuple[dict[Any, int], list[set[Any]]]:
    groups = [set(values) for values in (nx.weakly_connected_components(graph) if graph.is_directed() else nx.connected_components(graph))]
    groups.sort(key=lambda values: (-len(values), min((_node_sort_key(node) for node in values), default=("", ""))))
    node_component = {node: index for index, values in enumerate(groups) for node in values}
    return node_component, groups


def _empty_report(reason: str, *, detail: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "method_version": CANDIDATE_METHOD_VERSION,
        "candidates": [],
        "screening": {"status": "no_candidates", "reason": reason, "detail": detail, "screened_pairs": 0, "rejected": {}},
        "warnings": [],
    }


def _node_coordinates(graph: nx.Graph, node: Any) -> tuple[float, float] | None:
    attrs = graph.nodes[node]
    try:
        x, y = float(attrs["x"]), float(attrs["y"])
    except (KeyError, TypeError, ValueError):
        return None
    return (x, y) if math.isfinite(x) and math.isfinite(y) else None


def _in_area_nodes(data: OSMData, graph: nx.Graph) -> tuple[list[Any], dict[Any, Point]]:
    polygon = gpd.GeoSeries([data.area.polygon], crs="EPSG:4326").to_crs(data.area.working_crs).iloc[0]
    selected: list[Any] = []
    points: dict[Any, Point] = {}
    for node in sorted(graph.nodes, key=_node_sort_key):
        coords = _node_coordinates(graph, node)
        if coords is None:
            continue
        point = Point(coords)
        if polygon.covers(point):
            selected.append(node)
            points[node] = point
    return selected, points


def _nearest_screen_sources(nodes: list[Any], max_source_nodes: int) -> list[Any]:
    if len(nodes) <= max_source_nodes:
        return nodes
    if max_source_nodes == 1:
        return [nodes[len(nodes) // 2]]
    last = len(nodes) - 1
    indices = sorted({round(index * last / (max_source_nodes - 1)) for index in range(max_source_nodes)})
    return [nodes[index] for index in indices]


def _feature_intersections(
    data: OSMData,
    line_wgs84: LineString,
    layer_name: str,
) -> dict[str, Any]:
    frame = data.layers.get(layer_name)
    availability = data.layer_availability.get(layer_name, {}).get("status", "unknown")
    if frame is None or frame.crs is None or frame.empty and availability not in {"available", "no_features_returned"}:
        return {"status": "unknown", "feature_count": 0, "feature_ids": [], "reason": "Layer is missing or its coverage is unknown."}
    if frame.empty:
        return {"status": "no_intersection_observed", "feature_count": 0, "feature_ids": [], "reason": "The mapped layer query returned no features; this does not establish real-world absence."}
    try:
        projected = frame.to_crs(data.area.working_crs)
        line = gpd.GeoSeries([line_wgs84], crs="EPSG:4326").to_crs(data.area.working_crs).iloc[0]
        indexed_geometries = [
            (row_index, geometry)
            for row_index, geometry in enumerate(projected.geometry)
            if geometry is not None and not geometry.is_empty
        ]
        geometries = [geometry for _, geometry in indexed_geometries]
        if not geometries:
            return {"status": "unknown", "feature_count": int(len(frame)), "feature_ids": [], "reason": "Mapped layer has no usable geometry."}
        tree = STRtree(geometries)
        ids: list[str] = []
        for match in tree.query(line):
            index = int(match)
            if line.intersects(geometries[index]):
                row = projected.iloc[indexed_geometries[index][0]]
                feature_id = row.get("osm_id", row.get("osm_element_id", index))
                ids.append(str(feature_id))
        unique_ids = sorted(set(ids))
        return {
            "status": "mapped_obstacle_intersection" if unique_ids else "no_intersection_observed",
            "feature_count": int(len(frame)),
            "feature_ids": unique_ids[:20],
            "intersection_count": len(unique_ids),
            "reason": "Candidate line intersects mapped layer geometry." if unique_ids else "No intersection was found in this mapped layer; this is not proof of feasibility.",
        }
    except Exception as error:
        return {"status": "unknown", "feature_count": int(len(frame)), "feature_ids": [], "reason": f"Layer screening failed: {type(error).__name__}: {error}"}


def _issue_ids_for_nodes(issues: Iterable[Mapping[str, Any]], nodes: tuple[Any, Any]) -> list[str]:
    node_ids = {str(node) for node in nodes}
    related: list[str] = []
    for issue in issues:
        evidence_ids: set[str] = set()
        for evidence in issue.get("evidence", []) if isinstance(issue.get("evidence", []), list) else []:
            if not isinstance(evidence, Mapping):
                continue
            for key in ("osm_node_ids", "network_node_ids", "node_ids"):
                values = evidence.get(key, [])
                if isinstance(values, (list, tuple, set)):
                    evidence_ids.update(str(value) for value in values)
        if node_ids.intersection(evidence_ids) and issue.get("id"):
            related.append(str(issue["id"]))
    return sorted(set(related))


def _nearby_issue_associations(
    issues: Iterable[Mapping[str, Any]],
    line: LineString,
    *,
    working_crs: str,
    proximity_tolerance_m: float = 100.0,
) -> list[dict[str, Any]]:
    associations = []
    for issue in issues:
        issue_type = str(issue.get("type") or "")
        if not issue_type.startswith(("walk_poor_access_to_", "walk_excessive_detour_to_")):
            continue
        geometry_value = issue.get("geometry")
        if not isinstance(geometry_value, Mapping):
            continue
        try:
            issue_geometry = shape(geometry_value)
            issue_metric = gpd.GeoSeries([issue_geometry], crs="EPSG:4326").to_crs(working_crs).iloc[0]
            distance_m = float(line.distance(issue_metric))
        except Exception:
            continue
        if distance_m <= proximity_tolerance_m and issue.get("id"):
            associations.append({
                "issue_id": str(issue["id"]),
                "association_method": "candidate_geometry_within_tolerance_of_issue_summary_geometry",
                "distance_m": distance_m,
                "limitation": "Issue geometry summarizes mapped graph evidence; proximity does not prove this candidate fixes the issue.",
            })
    return sorted(associations, key=lambda item: (item["distance_m"], item["issue_id"]))


def _equivalent_endpoints(candidate: tuple[Point, Point], existing: tuple[Point, Point], tolerance_m: float = 15.0) -> bool:
    first, second = candidate
    left, right = existing
    return (
        (first.distance(left) <= tolerance_m and second.distance(right) <= tolerance_m)
        or (first.distance(right) <= tolerance_m and second.distance(left) <= tolerance_m)
    )


def discover_intervention_candidates(
    data: OSMData,
    *,
    issues: Iterable[Mapping[str, Any]] = (),
    max_candidates: int = DEFAULT_CANDIDATE_LIMIT,
    max_connection_length_m: float = MAX_CONNECTION_LENGTH_M,
    detour_ratio_threshold: float = DEFAULT_DETOUR_RATIO_THRESHOLD,
    max_screened_pairs: int = DEFAULT_MAX_SCREENED_PAIRS,
    max_source_nodes: int = DEFAULT_MAX_SOURCE_NODES,
    max_neighbors_per_source: int = DEFAULT_NEIGHBORS_PER_SOURCE,
) -> dict[str, Any]:
    """Find a small set of plausible graph-connectivity opportunities.

    The search uses a metric STRtree over nodes inside the selected polygon.
    It prioritizes weak-component gaps, one-way reachability gaps, then large
    route detours. The search is bounded by source, neighbor, and pair limits.
    Each output is a hypothetical graph edit requiring field verification.
    """
    if "walk" not in data.graphs:
        return _empty_report("missing_walking_graph", detail="Candidate discovery requires an available walking graph.")
    numeric_values = (max_connection_length_m, detour_ratio_threshold)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in numeric_values):
        raise ValueError("Candidate length and detour settings must be finite numbers.")
    if not (0 < max_connection_length_m <= MAX_CONNECTION_LENGTH_M):
        raise ValueError(f"max_connection_length_m must be in (0, {MAX_CONNECTION_LENGTH_M:g}] m.")
    if detour_ratio_threshold <= 1:
        raise ValueError("detour_ratio_threshold must be greater than 1.")
    for value, name, upper in (
        (max_candidates, "max_candidates", 50),
        (max_screened_pairs, "max_screened_pairs", 100_000),
        (max_source_nodes, "max_source_nodes", 5_000),
        (max_neighbors_per_source, "max_neighbors_per_source", 100),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > upper:
            raise ValueError(f"{name} must be an integer from 1 through {upper}.")

    source_graph = data.graphs["walk"]
    try:
        if not source_graph.graph.get("crs"):
            return _empty_report("missing_graph_crs", detail="Walking graph must declare its CRS.")
        source_crs = CRS.from_user_input(source_graph.graph["crs"])
        usable_nodes = []
        for node in source_graph.nodes:
            coords = _node_coordinates(source_graph, node)
            if coords is None:
                continue
            if source_crs.is_geographic and not (-180 <= coords[0] <= 180 and -90 <= coords[1] <= 90):
                continue
            usable_nodes.append(node)
        if len(usable_nodes) < source_graph.number_of_nodes():
            graph_for_projection = source_graph.subgraph(usable_nodes).copy()
        else:
            graph_for_projection = source_graph
        graph = project_graph(graph_for_projection, data.area.working_crs)
    except Exception as error:
        return _empty_report("invalid_walking_graph", detail=f"Could not prepare metric walking graph: {type(error).__name__}: {error}")
    if graph.number_of_nodes() < 2 or graph.number_of_edges() == 0:
        return _empty_report("insufficient_walking_graph", detail="At least two usable nodes and one edge are required.")
    bad_weights = []
    edge_iterator = graph.edges(keys=True, data=True) if graph.is_multigraph() else ((u, v, None, attrs) for u, v, attrs in graph.edges(data=True))
    for u, v, _, attrs in edge_iterator:
        try:
            length = float(attrs.get("length_m"))
        except (TypeError, ValueError):
            length = math.nan
        if not math.isfinite(length) or length < 0:
            bad_weights.append((u, v))
            if len(bad_weights) >= 5:
                break
    if bad_weights:
        return _empty_report("invalid_edge_length", detail=f"Walking graph contains invalid metric edge lengths; examples: {bad_weights!r}.")

    nodes, node_points = _in_area_nodes(data, graph)
    if len(nodes) < 2:
        return _empty_report("insufficient_in_area_nodes", detail="Fewer than two usable graph nodes lie inside the selected polygon.")
    points = [node_points[node] for node in nodes]
    tree = STRtree(points)
    index_to_node = {index: node for index, node in enumerate(nodes)}
    area_metric = gpd.GeoSeries([data.area.polygon], crs="EPSG:4326").to_crs(data.area.working_crs).iloc[0]
    component_for, _ = _components(graph)
    source_nodes = _nearest_screen_sources(nodes, max_source_nodes)
    reverse_graph = graph.reverse(copy=False) if graph.is_directed() else graph
    path_distance_cache: dict[Any, dict[Any, float]] = {}
    reverse_distance_cache: dict[Any, dict[Any, float]] = {}
    raw: list[dict[str, Any]] = []
    issue_list = list(issues)
    seen_pairs: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    rejected: Counter[str] = Counter()
    screened_pairs = 0

    for source in source_nodes:
        source_point = node_points[source]
        indexes = [int(index) for index in tree.query(source_point.buffer(max_connection_length_m))]
        neighbors = [index_to_node[index] for index in indexes if index_to_node[index] != source]
        neighbors.sort(key=lambda node: (source_point.distance(node_points[node]), _node_sort_key(node)))
        for target in neighbors[:max_neighbors_per_source]:
            if screened_pairs >= max_screened_pairs:
                break
            pair = tuple(sorted((_node_sort_key(source), _node_sort_key(target))))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            screened_pairs += 1
            target_point = node_points[target]
            direct_distance = float(source_point.distance(target_point))
            if not math.isfinite(direct_distance) or direct_distance <= 0:
                rejected["invalid_or_zero_link_length"] += 1
                continue
            if direct_distance > max_connection_length_m:
                rejected["over_maximum_link_length"] += 1
                continue
            if graph.has_edge(source, target) or graph.has_edge(target, source):
                rejected["already_directly_connected"] += 1
                continue
            line = LineString([source_point, target_point])
            if not area_metric.covers(line):
                rejected["outside_study_polygon"] += 1
                continue

            if component_for.get(source) != component_for.get(target):
                category = "disconnected_components"
                rationale = f"The endpoints are {direct_distance:.1f} m apart and belong to separate weakly connected walking components."
                directional_distances: dict[str, float | None] = {"start_to_end_m": None, "end_to_start_m": None}
                detour_ratio = None
            else:
                if source not in path_distance_cache:
                    path_distance_cache[source] = {
                        node: float(distance)
                        for node, distance in nx.single_source_dijkstra_path_length(graph, source, weight="length_m").items()
                    }
                if source not in reverse_distance_cache:
                    reverse_distance_cache[source] = {
                        node: float(distance)
                        for node, distance in nx.single_source_dijkstra_path_length(reverse_graph, source, weight="length_m").items()
                    }
                forward = path_distance_cache[source].get(target)
                backward = reverse_distance_cache[source].get(target)
                directional_distances = {
                    "start_to_end_m": forward,
                    "end_to_start_m": backward,
                }
                if forward is None or backward is None:
                    category = "directional_reachability_gap"
                    directions = []
                    if forward is None:
                        directions.append("start to end")
                    if backward is None:
                        directions.append("end to start")
                    rationale = f"The endpoints are {direct_distance:.1f} m apart; the mapped directed walking graph has no route {', '.join(directions)}."
                    detour_ratio = None
                else:
                    detour_ratio = max(forward, backward) / direct_distance
                    if not math.isfinite(detour_ratio) or detour_ratio <= detour_ratio_threshold:
                        rejected["no_material_detour"] += 1
                        continue
                    category = "excessive_route_detour"
                    rationale = f"The longest directed mapped route is {max(forward, backward):.1f} m for a {direct_distance:.1f} m direct reference (ratio {detour_ratio:.2f})."
            raw.append({
                "nodes": (source, target),
                "points": (source_point, target_point),
                "line": line,
                "length_m": direct_distance,
                "category": category,
                "rationale": rationale,
                "detour_ratio": detour_ratio,
                "directional_distances": directional_distances,
            })
        if screened_pairs >= max_screened_pairs:
            break

    for item in raw:
        endpoint_issue_ids = _issue_ids_for_nodes(issue_list, item["nodes"])
        nearby_associations = _nearby_issue_associations(issue_list, item["line"], working_crs=data.area.working_crs)
        item["related_issue_ids"] = sorted(set(endpoint_issue_ids).union(item["issue_id"] for item in nearby_associations))
        item["related_issue_associations"] = [
            {"issue_id": issue_id, "association_method": "candidate_endpoint_node_ids_present_in_issue_evidence"}
            for issue_id in endpoint_issue_ids
        ] + nearby_associations
        if nearby_associations:
            item["issue_selection_rationale"] = [
                f"Candidate geometry is within {association['distance_m']:.1f} m of a mapped access/detour issue summary geometry; association is proximity evidence only."
                for association in nearby_associations
            ]

    raw.sort(key=lambda item: (
        {"disconnected_components": 0, "directional_reachability_gap": 1, "excessive_route_detour": 2}[item["category"]],
        -len(item["related_issue_ids"]),
        -(item["detour_ratio"] or 0.0),
        item["length_m"],
        tuple(_node_sort_key(node) for node in item["nodes"]),
    ))
    selected: list[dict[str, Any]] = []
    for item in raw:
        if any(_equivalent_endpoints(item["points"], existing["points"]) for existing in selected):
            rejected["functionally_equivalent_candidate"] += 1
            continue
        selected.append(item)
        if len(selected) >= max_candidates:
            break

    candidate_records: list[dict[str, Any]] = []
    graph_source = source_graph.graph.get("arteria_source", "OpenStreetMap or imported graph")
    retrieved_at = source_graph.graph.get("arteria_retrieved_at") or data.metadata.get("retrieved_at")
    for item in selected:
        start_node, end_node = item["nodes"]
        start_attrs, end_attrs = graph.nodes[start_node], graph.nodes[end_node]
        start = [float(start_attrs["longitude"]), float(start_attrs["latitude"])]
        end = [float(end_attrs["longitude"]), float(end_attrs["latitude"])]
        line_wgs84 = LineString([start, end])
        building_screen = _feature_intersections(data, line_wgs84, "buildings")
        water_layer_name = next((name for name in ("water", "barriers") if name in data.layers), "water")
        water_screen = _feature_intersections(data, line_wgs84, water_layer_name)
        warnings = [
            "No field survey, property ownership, legal approval, accessibility standard, crossing safety, or construction review was performed.",
            "Missing mapped geometry is not evidence that a connection is physically feasible.",
        ]
        if building_screen["status"] == "mapped_obstacle_intersection":
            warnings.append("The hypothetical segment intersects mapped building geometry and needs detailed review.")
        if building_screen["status"] == "unknown":
            warnings.append("Building obstacle screening is unknown because mapped building geometry is unavailable or unusable.")
        missing_evidence = [
            "land ownership and access rights",
            "elevation, slope, and accessibility conditions",
            "field-verified pedestrian safety and construction constraints",
        ]
        if water_screen["status"] == "unknown":
            missing_evidence.append("water and other physical barrier geometry")
        node_ids = tuple(sorted(item["nodes"], key=_node_sort_key))
        seed = f"{CANDIDATE_METHOD_VERSION}|add_pedestrian_connection|{type(node_ids[0]).__name__}:{node_ids[0]}|{type(node_ids[1]).__name__}:{node_ids[1]}"
        candidate_id = "cand_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
        obstacle_present = building_screen["status"] == "mapped_obstacle_intersection" or water_screen["status"] == "mapped_obstacle_intersection"
        candidate_records.append({
            "candidate_id": candidate_id,
            "intervention": {"type": "add_pedestrian_connection", "start": start, "end": end},
            "start": {"node_id": str(start_node), "coordinates": start},
            "end": {"node_id": str(end_node), "coordinates": end},
            "geometry": geojson_geometry(item["line"], data.area.working_crs),
            "length_m": item["length_m"],
            "discovery": {
                "method": item["category"],
                "detour_ratio": item["detour_ratio"],
                "directed_route_distances_m": item["directional_distances"],
            },
            "related_issue_ids": item["related_issue_ids"],
            "related_issue_associations": item["related_issue_associations"],
            "selection_rationale": [item["rationale"], *item.get("issue_selection_rationale", [])],
            "screening": {
                "status": "candidate_with_mapped_obstacle_warnings" if obstacle_present else "candidate_requires_field_verification",
                "geometry_valid": True,
                "hard_constraints_passed": ["distinct graph endpoints", "maximum modeled link length", "straight segment inside the selected study polygon", "metric geometry is finite"],
                "mapped_buildings": building_screen,
                "mapped_water_or_barriers": water_screen,
                "physical_feasibility": "unknown",
                "missing_evidence": missing_evidence,
                "warnings": warnings,
            },
            "provenance": {
                "source": graph_source,
                "source_version": data.metadata.get("source_version", "unknown"),
                "retrieved_at": retrieved_at,
                "working_crs": data.area.working_crs,
                "method": CANDIDATE_METHOD_VERSION,
            },
            "assumptions": [
                "The added segment is a straight-line, bidirectional hypothetical pedestrian graph connection, matching the current scenario engine.",
                "OSM network and obstacle coverage may be incomplete.",
                "Candidate ranking is a graph-screening result, not a construction recommendation.",
            ],
            "candidate_generation_method_version": CANDIDATE_METHOD_VERSION,
        })

    report_warnings = [
        "Only add_pedestrian_connection interventions are generated; other intervention types are unsupported.",
        "Candidate screening does not establish legal, physical, safety, ownership, or construction feasibility.",
    ]
    return {
        "schema_version": 1,
        "method_version": CANDIDATE_METHOD_VERSION,
        "area_id": data.area.area_id,
        "candidate_intervention_types": ["add_pedestrian_connection"],
        "candidates": candidate_records,
        "screening": {
            "status": "candidates_found" if candidate_records else "no_candidates",
            "reason": None if candidate_records else "No candidate passed graph, geometry, and duplicate screening.",
            "study_area_node_count": len(nodes),
            "source_node_count_screened": len(source_nodes),
            "screened_pairs": screened_pairs,
            "candidate_count_before_limit": len(raw),
            "candidate_count_returned": len(candidate_records),
            "configured_limits": {
                "max_candidates": max_candidates,
                "max_connection_length_m": float(max_connection_length_m),
                "detour_ratio_threshold": float(detour_ratio_threshold),
                "max_screened_pairs": max_screened_pairs,
                "max_source_nodes": max_source_nodes,
                "max_neighbors_per_source": max_neighbors_per_source,
            },
            "rejected": dict(sorted(rejected.items())),
            "algorithm_complexity": "Spatial-index candidate lookup over a deterministic bounded source sample; shortest paths are computed at most once per screened source and its reverse graph.",
        },
        "warnings": report_warnings,
    }
