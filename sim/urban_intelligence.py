"""Bounded, deterministic urban problem detection over SIM evidence.

Findings describe the mapped graph and available OSM tags. They are screening
signals, not verified hazards, demand estimates, or construction instructions.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from typing import Any

import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point, shape
from shapely.ops import linemerge
from shapely.strtree import STRtree

from .analysis import analyze_snapshot, project_graph
from .geo import OSMData, _source_area_geometry_hash, geojson_geometry
from .impact import MAX_ROUTE_SAMPLE_COUNT, sample_route_pairs


URBAN_ISSUES_SCHEMA = "arteria.urban-issues.v1"
URBAN_ISSUES_METHOD_VERSION = "arteria.urban-problem-detection.v1"
MAX_URBAN_PROBLEMS = 24
MAX_COMPONENTS_TO_INSPECT = 40
MAX_COMPONENT_NODES_TO_INDEX = 500
DEFAULT_ROUTE_PAIR_SAMPLE_COUNT = 96
MAX_ROUTE_PAIR_SAMPLE_COUNT = min(128, MAX_ROUTE_SAMPLE_COUNT)
MAX_WGS84_VERTICES_PER_GEOMETRY = 512


def _stable_key(value: Any) -> tuple[str, str]:
    return type(value).__name__, str(value)


def _stable_id(prefix: str, *parts: Any) -> str:
    encoded = "\0".join(str(part) for part in parts).encode("utf-8")
    return prefix + hashlib.sha256(encoded).hexdigest()[:20]


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _coord_point(point: Point, crs: str) -> dict[str, Any] | None:
    try:
        result = geojson_geometry(point, crs)
        parsed = shape(result)
        if parsed.geom_type != "Point" or not parsed.is_valid:
            return None
        x, y = parsed.coords[0]
        if not (math.isfinite(x) and math.isfinite(y) and -180 <= x <= 180 and -90 <= y <= 90):
            return None
        return result
    except (TypeError, ValueError, OverflowError):
        return None


def _metric_point(attrs: Mapping[str, Any]) -> Point | None:
    x, y = _finite(attrs.get("x")), _finite(attrs.get("y"))
    if x is None or y is None:
        return None
    return Point(x, y)


def _valid_geojson(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    try:
        geometry = shape(value)
        if geometry.is_empty or not geometry.is_valid:
            return False
        if not all(math.isfinite(float(number)) for number in geometry.bounds):
            return False
        min_x, min_y, max_x, max_y = geometry.bounds
        return -180 <= min_x <= max_x <= 180 and -90 <= min_y <= max_y <= 90
    except Exception:
        return False


def _source_state(data: OSMData) -> tuple[str, str, bool | None]:
    source = str(data.metadata.get("source") or "unknown")
    if "fixture" in source.casefold() or "fixture" in str(data.metadata.get("source_version", "")).casefold():
        return source, "synthetic", None
    source_area = data.metadata.get("source_area")
    cache = data.metadata.get("cache")
    verified: bool | None = None
    if isinstance(source_area, Mapping):
        value = source_area.get("area_equivalence_verified", source_area.get("equivalence_verified"))
        if isinstance(value, bool):
            verified = value
        source_hash = source_area.get("source_geometry_sha256")
        if source_hash:
            verified = source_hash == _source_area_geometry_hash(data.area)
    if not isinstance(source_area, Mapping) or not source_area.get("source_geometry_sha256"):
        source_hash = data.metadata.get("source_area_geometry_sha256")
        if isinstance(source_hash, str):
            verified = source_hash == _source_area_geometry_hash(data.area)
    if verified is None and isinstance(cache, Mapping) and isinstance(cache.get("area_equivalence_verified"), bool):
        verified = cache["area_equivalence_verified"]
    if source == "OpenStreetMap" and verified is True:
        return source, "limited", True
    if source == "OpenStreetMap" and verified is False:
        return source, "low", False
    if source == "OpenStreetMap":
        return source, "limited", None
    return source, "low", verified


def _source_issue_map(analysis: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    issues = analysis.get("issues", [])
    if not isinstance(issues, list):
        return {}
    return {
        str(issue["id"]): issue
        for issue in issues
        if isinstance(issue, Mapping) and isinstance(issue.get("id"), str)
    }


def _candidate_records(candidate_evaluation: Any) -> list[Mapping[str, Any]]:
    if not isinstance(candidate_evaluation, Mapping):
        return []
    values = candidate_evaluation.get("ranked_candidates", [])
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, Mapping)]


def _candidate_issue_links(candidate_evaluation: Any, issue_id: str) -> list[str]:
    result = []
    for candidate in _candidate_records(candidate_evaluation):
        related = candidate.get("related_issue_ids", [])
        if isinstance(related, list) and issue_id in {str(item) for item in related}:
            candidate_id = candidate.get("candidate_id")
            if isinstance(candidate_id, str):
                result.append(candidate_id)
    return sorted(set(result))


def _candidate_component_links(
    candidate_evaluation: Any,
    source_nodes: set[str],
    target_nodes: set[str],
) -> list[str]:
    result = []
    for candidate in _candidate_records(candidate_evaluation):
        start = candidate.get("start")
        end = candidate.get("end")
        if not isinstance(start, Mapping) or not isinstance(end, Mapping):
            continue
        endpoints = {str(start.get("node_id")), str(end.get("node_id"))}
        if endpoints & source_nodes and endpoints & target_nodes:
            candidate_id = candidate.get("candidate_id")
            if isinstance(candidate_id, str):
                result.append(candidate_id)
    return sorted(set(result))


def _edge_geometry(graph: nx.Graph, origin: Any, destination: Any) -> LineString | None:
    edge_data = graph.get_edge_data(origin, destination)
    if not edge_data and not graph.is_directed():
        edge_data = graph.get_edge_data(destination, origin)
    if not edge_data:
        return None
    records = list(edge_data.values()) if graph.is_multigraph() else [edge_data]
    records.sort(key=lambda attrs: (_finite(attrs.get("length_m")) or math.inf, str(attrs.get("osmid", ""))))
    for attrs in records:
        geometry = attrs.get("geometry")
        if geometry is None:
            continue
        try:
            if geometry.geom_type == "MultiLineString":
                geometry = linemerge(geometry)
            if geometry.geom_type != "LineString" or geometry.is_empty or not geometry.is_valid:
                continue
            coords = list(geometry.coords)
        except (AttributeError, TypeError, ValueError):
            continue
        start = graph.nodes[origin]
        if all(key in start for key in ("x", "y")):
            start_point = Point(float(start["x"]), float(start["y"]))
            if start_point.distance(Point(coords[-1])) < start_point.distance(Point(coords[0])):
                coords.reverse()
        return LineString(coords)
    return None


def _mapped_path_geometry(graph: nx.Graph, path: list[Any]) -> dict[str, Any] | None:
    if len(path) < 2:
        return None
    coordinates: list[tuple[float, float]] = []
    for origin, destination in zip(path, path[1:]):
        segment = _edge_geometry(graph, origin, destination)
        if segment is None:
            return None
        coords = list(segment.coords)
        if coordinates and math.dist(coordinates[-1], coords[-1]) < math.dist(coordinates[-1], coords[0]):
            coords.reverse()
        if coordinates:
            join_distance = math.dist(coordinates[-1], coords[0])
            if join_distance > 2.0:
                return None
            if join_distance < 0.01:
                coords = coords[1:]
        coordinates.extend((float(x), float(y)) for x, y in coords)
    if len(coordinates) < 2 or len(coordinates) > MAX_WGS84_VERTICES_PER_GEOMETRY:
        return None
    geometry = geojson_geometry(LineString(coordinates), graph.graph["crs"])
    return geometry if _valid_geojson(geometry) else None


def _component_rows(graph: nx.Graph) -> list[set[Any]]:
    components = nx.weakly_connected_components(graph) if graph.is_directed() else nx.connected_components(graph)
    result = [set(item) for item in components]
    result.sort(key=lambda item: (-len(item), min((_stable_key(node) for node in item), default=("", ""))))
    return result


def _bounded_sorted(values: set[Any], limit: int) -> list[Any]:
    ordered = sorted(values, key=_stable_key)
    if len(ordered) <= limit:
        return ordered
    stride = (len(ordered) - 1) / (limit - 1) if limit > 1 else len(ordered)
    return [ordered[round(index * stride)] for index in range(limit)]


def _component_gap(
    graph: nx.Graph,
    smaller_nodes: set[Any],
    larger_nodes: set[Any],
) -> tuple[Any, Any, float] | None:
    targets = _bounded_sorted(larger_nodes, MAX_COMPONENT_NODES_TO_INDEX)
    sources = _bounded_sorted(smaller_nodes, MAX_COMPONENT_NODES_TO_INDEX)
    if not targets or not sources:
        return None
    target_pairs = [(node, _metric_point(graph.nodes[node])) for node in targets]
    target_pairs = [(node, point) for node, point in target_pairs if point is not None]
    targets = [node for node, _ in target_pairs]
    target_points = [point for _, point in target_pairs]
    sources = [node for node in sources if _metric_point(graph.nodes[node]) is not None]
    if not targets or not sources:
        return None
    tree = STRtree(target_points)
    best: tuple[float, tuple[str, str], tuple[str, str], Any, Any] | None = None
    for source in sources:
        point = _metric_point(graph.nodes[source])
        if point is None:
            continue
        for index in tree.query_nearest(point, all_matches=True):
            target_index = int(index)
            target = targets[target_index]
            distance = float(point.distance(target_points[target_index]))
            candidate = (distance, _stable_key(source), _stable_key(target), source, target)
            if best is None or candidate[:3] < best[:3]:
                best = candidate
    return (best[3], best[4], best[0]) if best is not None else None


def _area_boundary(data: OSMData):
    return gpd.GeoSeries([data.area.polygon], crs="EPSG:4326").to_crs(data.area.working_crs).iloc[0]


def _component_problems(
    data: OSMData,
    analysis: Mapping[str, Any],
    candidate_evaluation: Any,
    *,
    max_problems: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    raw_graph = data.graphs.get("walk")
    if not isinstance(raw_graph, nx.Graph) or raw_graph.number_of_nodes() < 2:
        return [], ["No usable walking graph was supplied; disconnected-network checks were not run."]
    if raw_graph.number_of_nodes() > 15_000:
        return [], ["Walking graph exceeded the 15,000-node urban issue inspection bound; component analysis was skipped."]
    try:
        graph = project_graph(raw_graph, data.area.working_crs)
        boundary = _area_boundary(data)
    except (ValueError, TypeError) as error:
        return [], [f"Walking graph could not be projected for issue detection ({type(error).__name__})."]
    components = _component_rows(graph)
    interior_nodes: set[Any] = set()
    for node, attrs in graph.nodes(data=True):
        point = _metric_point(attrs)
        if point is not None and boundary.covers(point):
            interior_nodes.add(node)
    if len(components) < 2 or not components[0] & interior_nodes:
        return [], []

    issue_records = _source_issue_map(analysis)
    known_disconnects = [
        (identifier, issue)
        for identifier, issue in issue_records.items()
        if str(issue.get("type", "")).startswith("disconnected_walk_component")
    ]
    output: list[dict[str, Any]] = []
    warnings: list[str] = []
    for component_index, component in enumerate(components[1:MAX_COMPONENTS_TO_INSPECT], start=1):
        interior_component = component & interior_nodes
        largest_interior = components[0] & interior_nodes
        if not interior_component or not largest_interior:
            continue
        gap = _component_gap(graph, interior_component, largest_interior)
        if gap is None:
            continue
        smaller_node, larger_node, gap_distance = gap
        smaller_attrs = graph.nodes[smaller_node]
        larger_attrs = graph.nodes[larger_node]
        smaller_point, larger_point = _metric_point(smaller_attrs), _metric_point(larger_attrs)
        if smaller_point is None or larger_point is None:
            continue
        midpoint = Point((smaller_point.x + larger_point.x) / 2, (smaller_point.y + larger_point.y) / 2)
        location = _coord_point(midpoint, data.area.working_crs)
        if location is None:
            continue
        gap_geometry = geojson_geometry(LineString([
            (smaller_point.x, smaller_point.y),
            (larger_point.x, larger_point.y),
        ]), data.area.working_crs)
        if not _valid_geojson(gap_geometry):
            continue
        boundary_distance = min(
            boundary.boundary.distance(smaller_point),
            boundary.boundary.distance(larger_point),
        )
        clipped_possible = boundary_distance <= 25.0
        in_area_count = len(interior_component)
        if clipped_possible:
            severity = "unknown"
            severity_basis = "A nearest gap endpoint lies within 25 m of the selected boundary; clipping may explain this mapped disconnection, so an ordinal severity is withheld."
        elif in_area_count >= 5 and gap_distance >= 300:
            severity = "high"
            severity_basis = "Graph-only ordinal rule: high requires at least 5 in-area mapped nodes in the separated component and a nearest-node straight-line gap of at least 300 m. This is not a safety or social-impact rating."
        elif in_area_count >= 2 or gap_distance >= 75:
            severity = "medium"
            severity_basis = "Graph-only ordinal rule: medium applies when the separated component has at least 2 in-area mapped nodes or the nearest-node straight-line gap is at least 75 m; this is not a safety or social-impact rating."
        else:
            severity = "low"
            severity_basis = "Graph-only ordinal rule: a one-node component with a nearest-node straight-line gap below 75 m is low; this is not a safety or social-impact rating."

        source_node_ids = {str(node) for node in interior_component}
        target_node_ids = {str(node) for node in largest_interior}
        matched_issue = None
        for identifier, issue in known_disconnects:
            issue_nodes = set()
            evidence = issue.get("evidence", [])
            if isinstance(evidence, list):
                for entry in evidence:
                    if isinstance(entry, Mapping) and isinstance(entry.get("osm_node_ids"), list):
                        issue_nodes.update(str(value) for value in entry["osm_node_ids"])
            if issue_nodes & source_node_ids:
                matched_issue = (identifier, issue)
                break
        issue_id = matched_issue[0] if matched_issue else None
        related_candidates = _candidate_component_links(candidate_evaluation, source_node_ids, target_node_ids)
        if issue_id:
            related_candidates = sorted(set(related_candidates + _candidate_issue_links(candidate_evaluation, issue_id)))
        evidence_id = _stable_id("ev_", data.area.area_id, "walk_component_gap", smaller_node, larger_node)
        gap_m = round(float(gap_distance), 3)
        description = (
            f"Graful pietonal OSM arată o componentă de {in_area_count} noduri cartografiate fără traseu către componenta principală. "
            f"Cele mai apropiate noduri din cele două componente sunt la aproximativ {gap_m:g} m în linie dreaptă; aceasta poate reflecta o întrerupere reală, tăierea grafului sau cartare incompletă și necesită verificare."
        )
        output.append({
            "problem_id": _stable_id("prob_", data.area.area_id, "pedestrian_disconnection", smaller_node, larger_node),
            "problem_type": "pedestrian_disconnection",
            "title": "Posibilă întrerupere a rețelei pietonale cartografiate",
            "description": description,
            "location": location,
            "geometry": gap_geometry,
            "geometry_meaning": "straight_line_gap_between_nearest_mapped_component_nodes; not a road or proposed construction alignment",
            "evidence": [{
                "evidence_id": evidence_id,
                "evidence_type": "weakly_connected_component_gap",
                "source": str(data.metadata.get("source") or "unknown"),
                "source_issue_id": issue_id,
                "component_index_by_size": component_index,
                "component_count": len(components),
                "component_node_count_in_study_area": in_area_count,
                "component_node_count_in_graph": len(component),
                "largest_component_node_count_in_study_area": len(largest_interior),
                "nearest_component_node_ids": [str(smaller_node), str(larger_node)],
                "nearest_gap_distance_m": gap_m,
                "nearest_node_search_sampled": len(interior_component) > MAX_COMPONENT_NODES_TO_INDEX or len(largest_interior) > MAX_COMPONENT_NODES_TO_INDEX,
                "boundary_distance_m": round(float(boundary_distance), 3),
                "possible_boundary_clipping": clipped_possible,
                "units": {"component_node_count_in_study_area": "node", "component_node_count_in_graph": "node", "component_count": "component", "nearest_gap_distance_m": "m", "boundary_distance_m": "m"},
            }],
            "severity": severity,
            "severity_basis": severity_basis,
            "data_confidence": _source_state(data)[1],
            "source": str(data.metadata.get("source") or "unknown"),
            "source_area_verification": "verified" if _source_state(data)[2] is True else "unverified" if _source_state(data)[2] is False else "unknown",
            "limitations": [
                "OSM graph connectivity is not a field-verified barrier or proof that a physical connection is absent.",
                "The straight-line gap is only a location cue, not a road, safe crossing, or buildable alignment.",
                "A nearby study-area boundary may create a clipping artifact.",
            ],
            "related_candidate_ids": related_candidates,
            "source_issue_ids": [issue_id] if issue_id else [],
        })
        if len(output) >= max_problems:
            break
    if len(components) - 1 > MAX_COMPONENTS_TO_INSPECT:
        warnings.append(f"Only the first {MAX_COMPONENTS_TO_INSPECT} disconnected components by deterministic size order were inspected.")
    return output, warnings


def _detour_problem(
    data: OSMData,
    graph: nx.Graph,
    origin: Any,
    destination: Any,
    *,
    ratio: float,
    network_distance: float,
    direct_distance: float,
    path: list[Any],
    candidate_evaluation: Any = None,
) -> dict[str, Any] | None:
    origin_attrs, destination_attrs = graph.nodes[origin], graph.nodes[destination]
    midpoint = Point(
        (float(origin_attrs["x"]) + float(destination_attrs["x"])) / 2,
        (float(origin_attrs["y"]) + float(destination_attrs["y"])) / 2,
    )
    location = _coord_point(midpoint, data.area.working_crs)
    if location is None:
        return None
    route_geometry = _mapped_path_geometry(graph, path)
    origin_id, destination_id = str(origin), str(destination)
    ratio_value, network_value, direct_value = round(ratio, 3), round(network_distance, 3), round(direct_distance, 3)
    if ratio >= 4.0 and network_distance >= 500:
        severity = "high"
        basis = "Calculated-pair ordinal rule: high requires a network/direct ratio >= 4.0 and network distance >= 500 m; this is not a safety rating."
    elif ratio >= 2.5 and network_distance >= 250:
        severity = "medium"
        basis = "Calculated-pair ordinal rule: medium requires a ratio >= 2.5 and network distance >= 250 m; this is not a safety rating."
    else:
        severity = "low"
        basis = "Calculated-pair ordinal rule: a qualifying route with ratio >= 2.0 that does not meet the medium/high thresholds is low; this is not a safety rating."
    evidence_id = _stable_id("ev_", data.area.area_id, "detour_pair", origin_id, destination_id)
    route_description = "Traseul pietonal calculat"
    description = (
        f"{route_description} între nodurile cartografiate {origin_id} și {destination_id} are {network_value:g} m față de {direct_value:g} m în linie dreaptă "
        f"(raport {ratio_value:g}). Eșantionul este determinist și limitat; rezultatul descrie numai graful OSM și nu indică un traseu periculos."
    )
    return {
        "problem_id": _stable_id("prob_", data.area.area_id, "excessive_pedestrian_detour", origin_id, destination_id),
        "problem_type": "excessive_pedestrian_detour",
        "title": "Ocolire pietonală în traseul calculat",
        "description": description,
        "location": location,
        "geometry": route_geometry,
        "geometry_meaning": "actual_mapped_graph_edge_path" if route_geometry else None,
        "evidence": [{
            "evidence_id": evidence_id,
            "evidence_type": "deterministic_graph_route_pair",
            "source": str(data.metadata.get("source") or "unknown"),
            "origin_node_id": origin_id,
            "destination_node_id": destination_id,
            "network_distance_m": network_value,
            "direct_distance_m": direct_value,
            "detour_ratio": ratio_value,
            "sample_method": "candidate-independent deterministic SIM node-pair hash sample",
            "route_geometry_status": "mapped_graph_edge_geometry" if route_geometry else "unavailable",
            "units": {"network_distance_m": "m", "direct_distance_m": "m", "detour_ratio": "ratio"},
        }],
        "severity": severity,
        "severity_basis": basis,
        "data_confidence": _source_state(data)[1],
        "source": str(data.metadata.get("source") or "unknown"),
        "source_area_verification": "verified" if _source_state(data)[2] is True else "unverified" if _source_state(data)[2] is False else "unknown",
        "limitations": [
            "The route pair is a deterministic analysis sample, not an observed journey or population sample.",
            "The direct distance is a reference only; it is not a feasible route or evidence of danger.",
            "OSM network coverage may omit mapped paths and crossings.",
        ],
        "related_candidate_ids": _candidate_pair_links(candidate_evaluation, origin_id, destination_id),
        "source_issue_ids": [],
    }


def _candidate_pair_links(candidate_evaluation: Any, origin_node_id: str, destination_node_id: str) -> list[str]:
    linked = []
    for candidate in _candidate_records(candidate_evaluation):
        start, end = candidate.get("start"), candidate.get("end")
        if not isinstance(start, Mapping) or not isinstance(end, Mapping):
            continue
        endpoints = {str(start.get("node_id")), str(end.get("node_id"))}
        if endpoints == {origin_node_id, destination_node_id}:
            candidate_id = candidate.get("candidate_id")
            if isinstance(candidate_id, str):
                linked.append(candidate_id)
    return sorted(set(linked))


def _sampled_detour_problems(
    data: OSMData,
    candidate_evaluation: Any = None,
    *,
    sample_count: int,
    detour_ratio_threshold: float,
    min_direct_distance_m: float,
    min_network_distance_m: float,
    max_problems: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    raw_graph = data.graphs.get("walk")
    sample_meta = {"requested_pair_count": sample_count, "sampled_pair_count": 0, "qualifying_pair_count": 0, "method": "candidate-independent deterministic SIM node-pair hash sample"}
    if not isinstance(raw_graph, nx.Graph) or raw_graph.number_of_nodes() < 2:
        return [], sample_meta, ["No usable walking graph was supplied; detour-pair analysis was not run."]
    if raw_graph.number_of_nodes() > 15_000:
        return [], sample_meta, ["Walking graph exceeded the 15,000-node detour inspection bound; sampled pair analysis was skipped."]
    try:
        graph = project_graph(raw_graph, data.area.working_crs)
        pairs = sample_route_pairs(
            data,
            sample_count=sample_count,
            seed=f"{URBAN_ISSUES_METHOD_VERSION}:{data.area.area_id}",
        )
    except (ValueError, TypeError) as error:
        return [], sample_meta, [f"Could not produce the bounded walking route-pair sample ({type(error).__name__})."]
    sample_meta["sampled_pair_count"] = len(pairs)
    rows: list[dict[str, Any]] = []
    for origin, destination in pairs:
        if origin not in graph or destination not in graph:
            continue
        first, second = graph.nodes[origin], graph.nodes[destination]
        first_point, second_point = _metric_point(first), _metric_point(second)
        if first_point is None or second_point is None:
            continue
        direct_distance = float(first_point.distance(second_point))
        if direct_distance < min_direct_distance_m:
            continue
        try:
            path = nx.shortest_path(graph, origin, destination, weight="length_m")
            network_distance = float(nx.shortest_path_length(graph, origin, destination, weight="length_m"))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
        if not math.isfinite(network_distance) or network_distance < min_network_distance_m:
            continue
        ratio = network_distance / direct_distance
        if not math.isfinite(ratio) or ratio < detour_ratio_threshold:
            continue
        problem = _detour_problem(
            data, graph, origin, destination, ratio=ratio, network_distance=network_distance,
            direct_distance=direct_distance, path=path, candidate_evaluation=candidate_evaluation,
        )
        if problem:
            rows.append(problem)
    sample_meta["qualifying_pair_count"] = len(rows)
    rows.sort(key=lambda row: (
        -float(row["evidence"][0]["detour_ratio"]),
        -float(row["evidence"][0]["network_distance_m"]),
        row["problem_id"],
    ))
    return rows[:max_problems], sample_meta, []


def _analysis_issue_problems(
    data: OSMData,
    analysis: Mapping[str, Any],
    candidate_evaluation: Any,
    *,
    max_problems: int,
) -> list[dict[str, Any]]:
    results = []
    issues = analysis.get("issues", [])
    if not isinstance(issues, list):
        return results
    for issue in issues:
        if not isinstance(issue, Mapping):
            continue
        issue_type = str(issue.get("type") or "")
        if issue_type.startswith("disconnected_"):
            continue
        if issue_type.startswith("walk_excessive_detour_to_"):
            problem_type = "excessive_detour_to_mapped_destination"
            category = issue_type.removeprefix("walk_excessive_detour_to_")
            title = "Ocolire față de o destinație cartografiată"
        elif issue_type.startswith("walk_poor_access_to_"):
            problem_type = "weak_access_to_mapped_destination"
            category = issue_type.removeprefix("walk_poor_access_to_")
            title = "Acces pietonal redus în graful cartografiat"
        else:
            continue
        geometry = issue.get("geometry")
        if not _valid_geojson(geometry):
            continue
        parsed = shape(geometry)
        point = parsed if parsed.geom_type == "Point" else parsed.representative_point()
        location = {"type": "Point", "coordinates": [float(point.x), float(point.y)]}
        identifier = str(issue.get("id") or "")
        if not identifier:
            continue
        metrics = issue.get("metrics", {}) if isinstance(issue.get("metrics"), Mapping) else {}
        evidence_id = _stable_id("ev_", data.area.area_id, "analysis_issue", identifier)
        severity = str(issue.get("severity") or "unknown")
        if severity not in {"low", "medium", "high"}:
            severity = "unknown"
        evidence = {
            "evidence_id": evidence_id,
            "evidence_type": "SIM_network_access_issue",
            "source": str(data.metadata.get("source") or "unknown"),
            "source_issue_id": identifier,
            "target_category": category,
            "metrics": dict(metrics),
            "coverage": dict(issue.get("data_coverage", {})) if isinstance(issue.get("data_coverage"), Mapping) else {},
        }
        if problem_type == "excessive_detour_to_mapped_destination":
            ratio = _finite(metrics.get("maximum_detour_ratio"))
            network_nodes = metrics.get("network_nodes_over_detour_threshold")
            total_nodes = metrics.get("study_area_network_nodes")
            basis = f"Severity inherited from SIM's bounded destination-detour analysis (threshold ratio > {metrics.get('threshold_ratio', 2.0)}); it reflects mapped-node counts, not risk."
        else:
            ratio = None
            unreachable = metrics.get("network_nodes_unreachable")
            total_nodes = metrics.get("network_node_count")
            basis = "Severity inherited from SIM's mapped-destination accessibility thresholds; node shares are not population access rates."
        source_issue_text = str(issue.get("description") or "")
        description = f"{source_issue_text} Categoria țintă: {category}. Rezultatul privește numai rețeaua și destinațiile mapate, nu cererea populației."
        results.append({
            "problem_id": _stable_id("prob_", data.area.area_id, problem_type, identifier),
            "problem_type": problem_type,
            "title": title,
            "description": description,
            "location": location,
            "geometry": dict(geometry),
            "geometry_meaning": "SIM analysis issue geometry in EPSG:4326",
            "evidence": [evidence],
            "severity": severity,
            "severity_basis": basis,
            "data_confidence": _source_state(data)[1],
            "source": str(data.metadata.get("source") or "unknown"),
            "source_area_verification": "verified" if _source_state(data)[2] is True else "unverified" if _source_state(data)[2] is False else "unknown",
            "limitations": [
                "Mapped OSM feature coverage may be incomplete; empty or unreachable records are not proof of real-world absence.",
                "Node counts do not represent residents, visits, or demand.",
                "This indicator is not a safety or danger assessment.",
            ],
            "related_candidate_ids": _candidate_issue_links(candidate_evaluation, identifier),
            "source_issue_ids": [identifier],
            "category": category,
        })
    results.sort(key=lambda item: (item["problem_type"], item["category"], item["problem_id"]))
    return results[:max_problems]


def _coverage_gaps(data: OSMData) -> list[dict[str, Any]]:
    categories = ("schools", "healthcare", "services", "public_transport", "green_space", "crossings", "buildings")
    by_category = data.metadata.get("feature_category_availability", {})
    result = []
    for category in categories:
        category_state = by_category.get(category) if isinstance(by_category, Mapping) else None
        if isinstance(category_state, Mapping):
            status = str(category_state.get("status") or "unknown")
            count = category_state.get("feature_count")
            query = category_state.get("source_query")
            retrieved = category_state.get("retrieved_at")
            warnings = category_state.get("warnings", [])
        else:
            layer_state = data.layer_availability.get(category, {})
            layer_status = str(layer_state.get("status") or "unknown") if isinstance(layer_state, Mapping) else "unknown"
            if layer_status == "available":
                continue
            status = "available_but_empty" if layer_status == "no_features_returned" else "unknown"
            count = layer_state.get("feature_count") if isinstance(layer_state, Mapping) else None
            query, retrieved, warnings = None, data.metadata.get("retrieved_at"), []
        if status in {"available", "not_requested"} and status != "not_requested":
            continue
        if status == "available" and (count is None or count > 0):
            continue
        explanation = (
            "No matching tagged records were returned from this bounded OSM query; this does not establish real-world absence."
            if status == "available_but_empty"
            else "Coverage is unknown or the category was not queried; no absence claim is supported."
        )
        result.append({
            "gap_id": _stable_id("gap_", data.area.area_id, category, status),
            "category_id": category,
            "status": status,
            "feature_count": count if isinstance(count, int) and not isinstance(count, bool) else None,
            "source_query": query,
            "source": str(data.metadata.get("source") or "unknown"),
            "retrieved_at": retrieved,
            "area_verification": "verified" if _source_state(data)[2] is True else "unverified" if _source_state(data)[2] is False else "unknown",
            "interpretation": explanation,
            "warnings": list(warnings)[:8] if isinstance(warnings, list) else [],
        })
    return result


def _verified_sumo_observation(data: OSMData, value: Any) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    if not isinstance(value, Mapping):
        return [], None
    status = str(value.get("status") or "unavailable")
    if status != "completed":
        return [], {"status": status, "metrics_available": False, "interpretation": "No completed paired simulation was supplied; no impact metrics were included."}
    area = value.get("study_area")
    source = value.get("source")
    verification = value.get("source_area_verification")
    comparison = value.get("comparison")
    baseline = value.get("baseline")
    scenario = value.get("scenario")
    if not all(isinstance(item, Mapping) for item in (area, source, verification, comparison, baseline, scenario)):
        return [], {"status": "rejected_unverifiable_result", "metrics_available": False, "interpretation": "The supplied simulation result lacks required provenance or completed-run fields."}
    source_area = source.get("source_area")
    source_hash = source_area.get("source_geometry_sha256") if isinstance(source_area, Mapping) else None
    expected_hash = _source_area_geometry_hash(data.area)
    area_geometry = area.get("geometry_wgs84")
    supplied_hash = None
    if isinstance(area_geometry, Mapping):
        try:
            supplied_hash = hashlib.sha256(shape(area_geometry).normalize().wkb).hexdigest()
        except Exception:
            supplied_hash = None
    verified = (
        area.get("area_id") == data.area.area_id
        and verification.get("status") == "verified"
        and source_hash == expected_hash
        and supplied_hash == expected_hash
        and baseline.get("status") == "completed"
        and scenario.get("status") == "completed"
    )
    metrics = comparison.get("metrics") if isinstance(comparison, Mapping) else None
    if not verified or not isinstance(metrics, Mapping):
        return [], {"status": "rejected_unverified_source_or_pair", "metrics_available": False, "interpretation": "Paired SUMO metrics were omitted because the source area, both runs, or comparison could not be verified against this study."}
    run_ids = [value.get("baseline_run_id"), value.get("scenario_run_id")]
    if not all(isinstance(run_id, str) and run_id for run_id in run_ids):
        return [], {"status": "rejected_unverified_run_ids", "metrics_available": False, "interpretation": "Paired SUMO metrics were omitted because stable run IDs were missing."}
    observation_metrics: dict[str, Any] = {}
    for metric_name, metric_value in metrics.items():
        if not isinstance(metric_value, Mapping):
            continue
        delta = _finite(metric_value.get("scenario_minus_baseline_mean"))
        before = _finite(metric_value.get("baseline_mean"))
        after = _finite(metric_value.get("scenario_mean"))
        if delta is None or before is None or after is None:
            continue
        observation_metrics[str(metric_name)] = {
            "baseline_mean": round(before, 6),
            "scenario_mean": round(after, 6),
            "scenario_minus_baseline_mean": round(delta, 6),
            "paired_vehicle_count": metric_value.get("paired_vehicle_count"),
        }
    if not observation_metrics:
        return [], {"status": "completed_no_comparable_metrics", "metrics_available": False, "interpretation": "Both runs completed, but no finite paired metric was available."}
    observation = {
        "observation_id": _stable_id("simobs_", data.area.area_id, *run_ids),
        "observation_type": "paired_sumo_simulation_difference",
        "source": "Eclipse SUMO paired simulation",
        "status": "calculated_simulation_output",
        "baseline_run_id": run_ids[0],
        "scenario_run_id": run_ids[1],
        "network_revision": value.get("network_revision"),
        "demand_type": "synthetic",
        "metrics": observation_metrics,
        "limitations": ["Synthetic demand and uncalibrated simulation; this is not measured city traffic, a forecast, or evidence of congestion."],
    }
    return [observation], {"status": "completed_verified_pair", "metrics_available": True}


def detect_urban_problems(
    data: OSMData,
    *,
    analysis: Mapping[str, Any] | None = None,
    candidate_evaluation: Any = None,
    paired_sumo_result: Any = None,
    max_problems: int = 12,
    route_pair_sample_count: int = DEFAULT_ROUTE_PAIR_SAMPLE_COUNT,
    detour_ratio_threshold: float = 2.0,
    min_direct_distance_m: float = 75.0,
    min_network_distance_m: float = 150.0,
) -> dict[str, Any]:
    """Return bounded localized problems and separate (non-problem) SUMO observations.

    Detour pairs are candidate-independent and share one deterministic sample
    across repeated calls for the same area and graph. Empty feature layers are
    emitted as coverage gaps, never converted into a confirmed absence.
    """
    if isinstance(max_problems, bool) or not isinstance(max_problems, int) or not 1 <= max_problems <= MAX_URBAN_PROBLEMS:
        raise ValueError(f"max_problems must be an integer from 1 through {MAX_URBAN_PROBLEMS}.")
    if isinstance(route_pair_sample_count, bool) or not isinstance(route_pair_sample_count, int) or not 1 <= route_pair_sample_count <= MAX_ROUTE_PAIR_SAMPLE_COUNT:
        raise ValueError(f"route_pair_sample_count must be an integer from 1 through {MAX_ROUTE_PAIR_SAMPLE_COUNT}.")
    ratio_threshold, direct_floor, network_floor = map(_finite, (detour_ratio_threshold, min_direct_distance_m, min_network_distance_m))
    if ratio_threshold is None or ratio_threshold <= 1 or direct_floor is None or direct_floor < 0 or network_floor is None or network_floor < 0:
        raise ValueError("Detour thresholds must be finite; the ratio must exceed 1 and distance thresholds must be non-negative.")
    if analysis is None:
        analysis = analyze_snapshot(data)
    if not isinstance(analysis, Mapping):
        raise ValueError("analysis must be a mapping returned by analyze_snapshot.")
    analysis_area = analysis.get("area")
    if not isinstance(analysis_area, Mapping) or analysis_area.get("area_id") != data.area.area_id:
        raise ValueError("analysis must match the supplied OSMData study area.")
    boundary = analysis_area.get("boundary")
    if not isinstance(boundary, Mapping):
        raise ValueError("analysis.area.boundary must contain valid EPSG:4326 geometry.")
    try:
        if hashlib.sha256(shape(boundary).normalize().wkb).hexdigest() != _source_area_geometry_hash(data.area):
            raise ValueError("analysis boundary does not match the supplied OSMData study area geometry.")
    except (TypeError, ValueError) as error:
        if isinstance(error, ValueError) and "does not match" in str(error):
            raise
        raise ValueError("analysis.area.boundary must be valid GeoJSON geometry.") from error

    warnings: list[str] = []
    components, component_warnings = _component_problems(data, analysis, candidate_evaluation, max_problems=max_problems)
    detours, sample, detour_warnings = _sampled_detour_problems(
        data,
        candidate_evaluation=candidate_evaluation,
        sample_count=route_pair_sample_count,
        detour_ratio_threshold=ratio_threshold,
        min_direct_distance_m=direct_floor,
        min_network_distance_m=network_floor,
        max_problems=max_problems,
    )
    analysis_issues = _analysis_issue_problems(data, analysis, candidate_evaluation, max_problems=max_problems)
    warnings.extend(component_warnings)
    warnings.extend(detour_warnings)

    priorities = {
        "pedestrian_disconnection": 0,
        "excessive_detour_to_mapped_destination": 1,
        "excessive_pedestrian_detour": 2,
        "weak_access_to_mapped_destination": 3,
    }
    problems = components + analysis_issues + detours
    problems.sort(key=lambda item: (
        priorities.get(str(item.get("problem_type")), 9),
        {"high": 0, "medium": 1, "low": 2, "unknown": 3}.get(str(item.get("severity")), 4),
        -float((item.get("evidence") or [{}])[0].get("detour_ratio", 0) or 0),
        str(item.get("problem_id", "")),
    ))
    problems = problems[:max_problems]
    for problem in problems:
        problem.pop("source_issue_ids", None)
        problem.pop("category", None)
        if not _valid_geojson(problem.get("location")):
            raise ValueError(f"Problem {problem.get('problem_id')} has invalid EPSG:4326 location geometry.")
        if problem.get("geometry") is not None and not _valid_geojson(problem["geometry"]):
            raise ValueError(f"Problem {problem.get('problem_id')} has invalid EPSG:4326 geometry.")

    observations, sumo_state = _verified_sumo_observation(data, paired_sumo_result)
    source, confidence, area_verified = _source_state(data)
    limitations = [
        "Findings describe the supplied OSM/network snapshot and do not establish physical hazards, access rights, legal status, or construction feasibility.",
        "OSM coverage and place extents may be incomplete; unreturned tags do not prove real-world absence.",
        "Graph-node pair samples are calculated network probes, not observed journeys, population samples, or demand.",
    ]
    if area_verified is False:
        limitations.append("The cached source-area equivalence is unverified; map positions and problem localization should be treated as low-confidence until the original source polygon is confirmed.")
        warnings.append("Source area equivalence is unverified; all problem locations inherit low geographic confidence.")
    return {
        "schema_version": URBAN_ISSUES_SCHEMA,
        "method_version": URBAN_ISSUES_METHOD_VERSION,
        "area_id": data.area.area_id,
        "area_geometry_sha256": _source_area_geometry_hash(data.area),
        "source": source,
        "retrieved_at": data.metadata.get("retrieved_at"),
        "source_area_verification": "verified" if area_verified is True else "unverified" if area_verified is False else "unknown",
        "data_confidence": confidence,
        "thresholds": {
            "detour_ratio_threshold": ratio_threshold,
            "min_direct_distance_m": direct_floor,
            "min_network_distance_m": network_floor,
            "route_pair_sample_count": route_pair_sample_count,
        },
        "sample": sample,
        "problems": problems,
        "coverage_gaps": _coverage_gaps(data),
        "simulation_observations": observations,
        "simulation_status": sumo_state,
        "warnings": sorted(set(warnings)),
        "limitations": limitations,
    }


def problem_locations_geojson(urban_issues: Mapping[str, Any]) -> dict[str, Any]:
    """Export actual problem geometries and representative locations as WGS84 GeoJSON."""
    if not isinstance(urban_issues, Mapping) or urban_issues.get("schema_version") != URBAN_ISSUES_SCHEMA:
        raise ValueError(f"urban_issues must use {URBAN_ISSUES_SCHEMA}.")
    features = []
    problems = urban_issues.get("problems", [])
    if not isinstance(problems, list):
        raise ValueError("urban_issues.problems must be an array.")
    for item in problems:
        if not isinstance(item, Mapping) or not isinstance(item.get("problem_id"), str):
            continue
        properties = {
            "problem_id": item["problem_id"],
            "problem_type": item.get("problem_type"),
            "title": item.get("title"),
            "severity": item.get("severity"),
            "severity_basis": item.get("severity_basis"),
            "data_confidence": item.get("data_confidence"),
            "source": item.get("source"),
            "related_candidate_ids": item.get("related_candidate_ids", []),
        }
        geometry = item.get("geometry")
        if geometry is not None:
            if not _valid_geojson(geometry):
                raise ValueError(f"Problem {item['problem_id']} has invalid WGS84 geometry.")
            features.append({"type": "Feature", "id": f"{item['problem_id']}:geometry", "geometry": geometry, "properties": {**properties, "layer": "problem_geometry", "geometry_meaning": item.get("geometry_meaning")}})
        location = item.get("location")
        if location is not None:
            if not _valid_geojson(location) or shape(location).geom_type != "Point":
                raise ValueError(f"Problem {item['problem_id']} has invalid WGS84 location point.")
            features.append({"type": "Feature", "id": f"{item['problem_id']}:location", "geometry": location, "properties": {**properties, "layer": "problem_location"}})
    features.sort(key=lambda feature: (feature["properties"]["problem_id"], feature["properties"]["layer"]))
    return {
        "type": "FeatureCollection",
        "metadata": {
            "schema_version": "arteria.urban-problem-geojson.v1",
            "area_id": urban_issues.get("area_id"),
            "crs": "EPSG:4326",
            "source": urban_issues.get("source"),
            "retrieved_at": urban_issues.get("retrieved_at"),
            "source_area_verification": urban_issues.get("source_area_verification"),
            "attribution": "© OpenStreetMap contributors" if urban_issues.get("source") == "OpenStreetMap" else None,
            "license": "ODbL-1.0" if urban_issues.get("source") == "OpenStreetMap" else None,
            "feature_count": len(features),
            "limitations": urban_issues.get("limitations", []),
        },
        "features": features,
    }
