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


CANDIDATE_METHOD_VERSION = "arteria-pedestrian-candidates-v2.1"
DEFAULT_CANDIDATE_LIMIT = 3
DEFAULT_CANDIDATE_POOL_LIMIT = 100
MAX_CANDIDATE_POOL_LIMIT = 500
MAX_SCREENED_FEATURE_DETAILS = 30
MATERIAL_BUILDING_OVERLAP_M = 0.5
GEOMETRY_CONTACT_TOLERANCE_M = 0.02
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


def _source_area_verified(data: OSMData) -> bool:
    cache = data.metadata.get("cache", {})
    if isinstance(cache, Mapping) and cache.get("area_equivalence_verified") is not None:
        return bool(cache.get("area_equivalence_verified"))
    if isinstance(cache, Mapping) and cache.get("area_key_matches") is False:
        return False
    if isinstance(cache, Mapping) and cache.get("area_key_matches") is True:
        return True
    source_key = data.metadata.get("area_key")
    current_key = data.metadata.get("current_area_key")
    return source_key == current_key if source_key and current_key else True


def _prepare_feature_index(data: OSMData, layer_name: str) -> dict[str, Any]:
    frame = data.layers.get(layer_name)
    availability = data.layer_availability.get(layer_name, {}).get("status", "unknown")
    verified_area = _source_area_verified(data)
    if frame is None or frame.crs is None or availability not in {"available", "no_features_returned"}:
        return {"layer_name": layer_name, "frame": frame, "status": "unknown", "feature_count": 0 if frame is None else int(len(frame)), "reason": "Layer is missing or its coverage is unknown.", "verified_area": verified_area, "geometries": [], "records": [], "tree": None, "quality": {}}
    if frame.empty:
        empty_status = "no_features_returned" if verified_area else "unknown_source_area_unverified"
        return {"layer_name": layer_name, "frame": frame, "status": empty_status, "feature_count": 0, "reason": "The mapped layer query returned no features; this does not establish real-world absence." if verified_area else "The cached layer has no features and its source area is unverified.", "verified_area": verified_area, "geometries": [], "records": [], "tree": None, "quality": {}}
    try:
        projected = frame.to_crs(data.area.working_crs)
        records: list[dict[str, Any]] = []
        geometries = []
        polygon_count = 0
        quality: Counter[str] = Counter()
        identities: dict[tuple[str, str], dict[str, Any]] = {}
        for row_index, geometry in enumerate(projected.geometry):
            row = projected.iloc[row_index]
            osm_id = row.get("osm_id", row.get("osm_element_id"))
            element_type = row.get("osm_element_type", "")
            identity = (str(element_type or ""), str(osm_id)) if osm_id is not None else ("row", str(row_index))
            if geometry is None or geometry.is_empty:
                quality["null_or_empty_geometry_count"] += 1
                continue
            valid = bool(geometry.is_valid)
            if not valid:
                quality["invalid_geometry_count"] += 1
            if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                quality["nonpolygon_geometry_count"] += 1
            else:
                polygon_count += 1
            previous = identities.get(identity)
            if previous is not None:
                if previous["geometry"].equals(geometry):
                    quality["duplicate_record_count"] += 1
                    continue
                quality["ambiguous_duplicate_identity_count"] += 1
                previous["ambiguous_identity"] = True
            record = {"geometry": geometry, "feature_id": str(osm_id) if osm_id is not None else str(row_index), "identity": identity, "row_index": row_index, "ambiguous_identity": previous is not None, "geometry_valid": valid, "polygonal": geometry.geom_type in {"Polygon", "MultiPolygon"}}
            identities.setdefault(identity, record)
            geometries.append(geometry)
            records.append(record)
        tree = STRtree(geometries) if geometries else None
        if not geometries:
            status = "unknown_source_area_unverified" if not verified_area else "unknown"
            reason = "No usable polygon geometry was found in the mapped layer."
        else:
            status, reason = "available", "Mapped polygon geometries are available for screening."
        return {"layer_name": layer_name, "frame": frame, "status": status, "feature_count": int(len(frame)), "polygon_count": polygon_count, "reason": reason, "verified_area": verified_area, "geometries": geometries, "records": records, "tree": tree, "quality": dict(sorted(quality.items())), "working_crs": data.area.working_crs}
    except Exception as error:
        return {"layer_name": layer_name, "frame": frame, "status": "unknown", "feature_count": int(len(frame)), "reason": f"Layer screening failed: {type(error).__name__}: {error}", "verified_area": verified_area, "geometries": [], "records": [], "tree": None, "quality": {}}


def _line_intersection_class(line: LineString, polygon: Any) -> tuple[str | None, float]:
    if any(
        polygon.contains(point) and polygon.boundary.distance(point) > GEOMETRY_CONTACT_TOLERANCE_M
        for point in (Point(line.coords[0]), Point(line.coords[-1]))
    ):
        return "endpoint_inside", 0.0
    intersection = line.intersection(polygon)
    if intersection.is_empty:
        return None, 0.0
    segments = []
    if intersection.geom_type == "LineString":
        segments = [intersection]
    elif intersection.geom_type == "MultiLineString":
        segments = list(intersection.geoms)
    elif intersection.geom_type == "GeometryCollection":
        segments = [part for part in intersection.geoms if part.geom_type == "LineString"]
    interior_length = sum(
        float(part.length)
        for part in segments
        if part.length > 0
        and polygon.contains(part.interpolate(0.5, normalized=True))
        and polygon.boundary.distance(part.interpolate(0.5, normalized=True)) > GEOMETRY_CONTACT_TOLERANCE_M
    )
    if interior_length >= MATERIAL_BUILDING_OVERLAP_M:
        return "interior_crossing", interior_length
    if interior_length > 0:
        return "short_interior_overlap_requires_review", interior_length
    return "boundary_only_contact", 0.0


def _feature_intersections(index: Mapping[str, Any], line: LineString) -> dict[str, Any]:
    layer_name = str(index.get("layer_name", "mapped layer"))
    frame = index.get("frame")
    feature_count = int(index.get("feature_count", 0))
    if index.get("status") in {"unknown", "unknown_source_area_unverified", "no_features_returned"}:
        if index.get("status") == "no_features_returned":
            return {"status": "no_intersection_observed", "classification": "no_mapped_conflict_observed", "feature_count": 0, "feature_ids": [], "intersection_count": 0, "intersections": [], "quality": {}, "reason": "The mapped layer query returned no features; this does not establish real-world absence."}
        status = "unknown_source_area_unverified" if index.get("status") == "unknown_source_area_unverified" else "unknown"
        return {"status": status, "classification": status, "feature_count": feature_count, "feature_ids": [], "intersection_count": 0, "intersections": [], "quality": dict(index.get("quality", {})), "reason": str(index.get("reason", "Mapped coverage is unknown."))}
    try:
        # The index and candidate geometry use the study area's metric CRS.
        metric_line = gpd.GeoSeries([line], crs="EPSG:4326").to_crs(index["working_crs"]).iloc[0]
        hits: list[dict[str, Any]] = []
        for match in index["tree"].query(metric_line.buffer(GEOMETRY_CONTACT_TOLERANCE_M)):
            record = index["records"][int(match)]
            polygon = record["geometry"]
            try:
                if not metric_line.intersects(polygon):
                    if metric_line.distance(polygon) > GEOMETRY_CONTACT_TOLERANCE_M:
                        continue
                    if record["polygonal"] and record["geometry_valid"] and not record["ambiguous_identity"]:
                        hits.append({"feature_id": record["feature_id"], "classification": "boundary_only_contact", "interior_overlap_m": 0.0, "identity_ambiguous": False})
                        continue
            except Exception:
                try:
                    if not metric_line.intersects(polygon.envelope):
                        continue
                except Exception:
                    continue
                record = {**record, "geometry_valid": False}
            if not record["geometry_valid"] or not record["polygonal"] or record["ambiguous_identity"]:
                hits.append({"feature_id": record["feature_id"], "classification": "ambiguous_invalid_feature", "interior_overlap_m": 0.0, "identity_ambiguous": bool(record["ambiguous_identity"])})
                continue
            classification, overlap_m = _line_intersection_class(metric_line, polygon)
            if classification is None:
                continue
            hits.append({"feature_id": record["feature_id"], "classification": classification, "interior_overlap_m": round(overlap_m, 3), "identity_ambiguous": bool(record["ambiguous_identity"])})
        hits.sort(key=lambda hit: (hit["classification"], hit["feature_id"]))
        unique_ids = sorted({hit["feature_id"] for hit in hits})
        classifications = Counter(hit["classification"] for hit in hits)
        material = classifications["interior_crossing"] + classifications["endpoint_inside"]
        if material:
            classification = "mapped_material_conflict"
            status = "mapped_obstacle_intersection"
        elif classifications["ambiguous_invalid_feature"]:
            classification = "ambiguous_invalid_feature"
            status = "ambiguous_obstacle_geometry"
        elif hits:
            classification = hits[0]["classification"] if len(classifications) == 1 else "mixed_review_intersections"
            status = "conditional_review"
        elif not index.get("verified_area", True):
            classification, status = "unknown_source_area_unverified", "unknown_source_area_unverified"
        elif index.get("polygon_count", 0) == 0:
            classification, status = "unknown_invalid_feature_geometry", "unknown"
        elif index.get("quality", {}).get("null_or_empty_geometry_count", 0):
            classification, status = "unknown_invalid_feature_geometry", "unknown"
        else:
            classification, status = "no_mapped_conflict_observed", "no_intersection_observed"
        reason = "Candidate intersects mapped geometry with a material interior or endpoint conflict." if material else "Candidate intersects a mapped feature whose geometry or identity is ambiguous." if classifications["ambiguous_invalid_feature"] else "Mapped layer screening found no material interior conflict; incomplete mapping and field conditions still require review."
        return {"status": status, "classification": classification, "feature_count": feature_count, "feature_ids": unique_ids[:20], "intersection_count": len(unique_ids), "classification_counts": dict(sorted(classifications.items())), "intersections": hits[:MAX_SCREENED_FEATURE_DETAILS], "quality": dict(index.get("quality", {})), "reason": reason}
    except Exception as error:
        return {"status": "unknown", "classification": "unknown", "feature_count": feature_count, "feature_ids": [], "intersection_count": 0, "intersections": [], "quality": dict(index.get("quality", {})), "reason": f"Layer screening failed: {type(error).__name__}: {error}"}


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
    candidate_pool_limit: int = DEFAULT_CANDIDATE_POOL_LIMIT,
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
    A bounded pool is obstacle-screened before a final shortlist is selected.
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
        (candidate_pool_limit, "candidate_pool_limit", MAX_CANDIDATE_POOL_LIMIT),
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
    component_for, component_groups = _components(graph)
    component_area_counts: Counter[int] = Counter(component_for[node] for node in nodes)
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
                "component_sizes": [len(component_groups[component_for[node]]) for node in (source, target)],
                "component_in_area_node_counts": [component_area_counts[component_for[node]] for node in (source, target)],
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
        -(item["detour_ratio"] or 0.0),
        item["length_m"],
        tuple(_node_sort_key(node) for node in item["nodes"]),
    ))
    deduplicated: list[dict[str, Any]] = []
    for item in raw:
        if any(_equivalent_endpoints(item["points"], existing["points"]) for existing in deduplicated):
            rejected["functionally_equivalent_candidate"] += 1
            continue
        deduplicated.append(item)

    pool = deduplicated[:candidate_pool_limit]
    building_index = _prepare_feature_index(data, "buildings")
    water_layer_name = next((name for name in ("water", "barriers") if name in data.layers), "water")
    water_index = _prepare_feature_index(data, water_layer_name)

    screened_records: list[dict[str, Any]] = []
    eligible_records: list[dict[str, Any]] = []
    graph_source = source_graph.graph.get("arteria_source", "OpenStreetMap or imported graph")
    retrieved_at = source_graph.graph.get("arteria_retrieved_at") or data.metadata.get("retrieved_at")
    blocked_counts: Counter[str] = Counter()
    for item in pool:
        start_node, end_node = item["nodes"]
        start_attrs, end_attrs = graph.nodes[start_node], graph.nodes[end_node]
        start = [float(start_attrs["longitude"]), float(start_attrs["latitude"])]
        end = [float(end_attrs["longitude"]), float(end_attrs["latitude"])]
        line_wgs84 = LineString([start, end])
        building_screen = _feature_intersections(building_index, line_wgs84)
        water_screen = _feature_intersections(water_index, line_wgs84)
        warnings = [
            "No field survey, property ownership, legal approval, accessibility standard, crossing safety, or construction review was performed.",
            "Missing mapped geometry is not evidence that a connection is physically feasible.",
        ]
        if building_screen["classification"] == "mapped_material_conflict":
            warnings.append("The hypothetical segment has a mapped material building conflict and is excluded from the eligible shortlist.")
        if building_screen["classification"] == "ambiguous_invalid_feature":
            warnings.append("The hypothetical segment intersects an invalid or ambiguous building-layer feature and is excluded from the eligible shortlist.")
        if water_screen["classification"] in {"mapped_material_conflict", "ambiguous_invalid_feature"}:
            warnings.append("The hypothetical segment intersects mapped water or barrier geometry and is excluded from the eligible shortlist.")
        if building_screen["status"] in {"unknown", "unknown_source_area_unverified"}:
            warnings.append("Building obstacle screening is unknown because mapped building geometry is unavailable or unusable.")
        if building_screen["status"] == "conditional_review":
            warnings.append("Building contact or a short interior overlap requires geometry and field review.")
        missing_evidence = [
            "land ownership and access rights",
            "elevation, slope, and accessibility conditions",
            "field-verified pedestrian safety and construction constraints",
        ]
        if water_screen["status"] in {"unknown", "unknown_source_area_unverified"}:
            missing_evidence.append("water and other physical barrier geometry")
        node_ids = tuple(sorted(item["nodes"], key=_node_sort_key))
        seed = f"{CANDIDATE_METHOD_VERSION}|add_pedestrian_connection|{type(node_ids[0]).__name__}:{node_ids[0]}|{type(node_ids[1]).__name__}:{node_ids[1]}"
        candidate_id = "cand_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
        building_blocked = building_screen["classification"] in {"mapped_material_conflict", "ambiguous_invalid_feature"}
        water_blocked = water_screen["classification"] in {"mapped_material_conflict", "ambiguous_invalid_feature"}
        blocked = building_blocked or water_blocked
        material_conflict = building_screen["classification"] == "mapped_material_conflict" or water_screen["classification"] == "mapped_material_conflict"
        if building_screen["classification"] == "mapped_material_conflict":
            blocked_counts["material_building_conflict"] += 1
        if building_screen["classification"] == "ambiguous_invalid_feature":
            blocked_counts["ambiguous_building_geometry"] += 1
        if water_screen["classification"] in {"mapped_material_conflict", "ambiguous_invalid_feature"}:
            blocked_counts["mapped_water_or_barrier_conflict"] += 1
        candidate = {
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
                "endpoint_component_sizes": item["component_sizes"],
                "endpoint_component_in_area_node_counts": item["component_in_area_node_counts"],
                "small_component_caution": any(value <= 3 for value in item["component_in_area_node_counts"]),
            },
            "related_issue_ids": item["related_issue_ids"],
            "related_issue_associations": item["related_issue_associations"],
            "selection_rationale": [item["rationale"], *item.get("issue_selection_rationale", [])],
            "screening": {
                "status": "rejected_mapped_obstacle_conflict" if blocked else "conditional_candidate_requires_field_review",
                "eligibility": "blocked" if blocked else "conditional",
                "recommendation_status": "not_eligible" if blocked else "conditional_candidate_requires_field_review",
                "geometry_valid": True,
                "hard_constraints_passed": ["distinct graph endpoints", "maximum modeled link length", "straight segment inside the selected study polygon", "metric geometry is finite"],
                "mapped_buildings": building_screen,
                "mapped_water_or_barriers": water_screen,
                "physical_feasibility": "unknown",
                "material_conflict": material_conflict,
                "mapped_obstacle_conflict": blocked,
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
        }
        if blocked:
            candidate["screening"]["exclusion_reasons"] = [
                reason for condition, reason in (
                    (building_screen["classification"] == "mapped_material_conflict", "mapped_material_building_conflict"),
                    (building_screen["classification"] == "ambiguous_invalid_feature", "ambiguous_or_invalid_building_feature"),
                    (water_blocked, "mapped_water_or_barrier_conflict"),
                ) if condition
            ]
            screened_records.append(candidate)
        else:
            eligible_records.append(candidate)

    report_warnings = [
        "Only add_pedestrian_connection interventions are generated; other intervention types are unsupported.",
        "Candidate screening does not establish legal, physical, safety, ownership, or construction feasibility.",
        "Candidates in the shortlist remain conditional until field, ownership, accessibility, and safety checks are complete.",
    ]
    candidate_records = eligible_records[:max_candidates]
    if any(candidate["discovery"]["small_component_caution"] for candidate in candidate_records):
        report_warnings.append("Some opportunities touch a component with three or fewer in-area nodes; graph and boundary artifacts require review.")
    return {
        "schema_version": 1,
        "method_version": CANDIDATE_METHOD_VERSION,
        "area_id": data.area.area_id,
        "candidate_intervention_types": ["add_pedestrian_connection"],
        "candidates": candidate_records,
        "eligible_candidates": eligible_records,
        "screened_candidates": screened_records[:MAX_CANDIDATE_POOL_LIMIT],
        "screening": {
            "status": "conditional_candidates_found" if candidate_records else "no_eligible_candidates",
            "reason": None if candidate_records else "No candidate passed material building and mapped barrier conflict screening within the bounded opportunity pool.",
            "study_area_node_count": len(nodes),
            "source_node_count_screened": len(source_nodes),
            "screened_pairs": screened_pairs,
            "candidate_count_before_limit": len(raw),
            "candidate_count_deduplicated": len(deduplicated),
            "candidate_pool_count": len(pool),
            "candidate_pool_limit": candidate_pool_limit,
            "candidate_count_screened": len(pool),
            "candidate_count_eligible_conditional": len(eligible_records),
            "candidate_count_rejected_conflict": len(screened_records),
            "candidate_count_rejected_material_conflict": blocked_counts["material_building_conflict"],
            "candidate_count_rejected_ambiguous_building_geometry": blocked_counts["ambiguous_building_geometry"],
            "candidate_count_rejected_mapped_barrier_conflict": blocked_counts["mapped_water_or_barrier_conflict"],
            "candidate_count_returned": len(candidate_records),
            "final_shortlist_is_conditional": bool(candidate_records),
            "screening_truncated_count": max(0, len(deduplicated) - len(pool)),
            "configured_limits": {
                "max_candidates": max_candidates,
                "max_connection_length_m": float(max_connection_length_m),
                "detour_ratio_threshold": float(detour_ratio_threshold),
                "max_screened_pairs": max_screened_pairs,
                "max_source_nodes": max_source_nodes,
                "max_neighbors_per_source": max_neighbors_per_source,
            },
            "rejected": dict(sorted(rejected.items())),
            "material_conflict_rejected": dict(sorted(blocked_counts.items())),
            "algorithm_complexity": "Spatial-index candidate lookup over a deterministic bounded source sample; shortest paths are computed at most once per screened source and its reverse graph.",
        },
        "warnings": report_warnings,
    }
