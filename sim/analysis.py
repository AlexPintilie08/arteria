"""Deterministic network connectivity, accessibility, and issue analysis."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from typing import Any, Iterable

import geopandas as gpd
import networkx as nx
import osmnx as ox
from pyproj import CRS
from shapely import STRtree
from shapely.geometry import LineString, MultiPoint, Point

from .geo import OSMData, StudyArea, feature_collection, geojson_geometry


WALK_SPEED_MPS = 1.3
BIKE_SPEED_MPS = 4.5
DEFAULT_ACCESS_THRESHOLD_MINUTES = 15.0
MAX_HEATMAP_FEATURES = 500
MAX_ISSUE_GEOMETRY_POINTS = 250


class RouteError(ValueError):
    """Raised for invalid nodes or route parameters."""


def _node_sort_key(node: Any) -> tuple[str, str]:
    return type(node).__name__, str(node)


def _edge_length(attrs: dict[str, Any], crs: CRS | None = None) -> float | None:
    value = attrs.get("length_m")
    try:
        length = float(value)
    except (TypeError, ValueError):
        length = math.nan
    if math.isfinite(length) and length >= 0:
        return length
    value = attrs.get("length")
    try:
        length = float(value)
    except (TypeError, ValueError):
        return None
    if crs is not None and crs.is_projected and crs.axis_info:
        length *= float(crs.axis_info[0].unit_conversion_factor)
    if math.isfinite(length) and length >= 0:
        return length
    return None


def normalize_graph(graph: nx.Graph) -> nx.Graph:
    """Copy a graph and expose normalized metric edge lengths and lon/lat."""
    result = graph.copy()
    crs_value = result.graph.get("crs")
    if crs_value is None:
        raise ValueError("Network graph must declare graph.graph['crs'].")
    source_crs = CRS.from_user_input(crs_value)
    if source_crs.is_geographic:
        from pyproj import Transformer

        to_wgs84 = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
    else:
        from pyproj import Transformer

        to_wgs84 = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
    for _, attrs in result.nodes(data=True):
        if "x" not in attrs or "y" not in attrs:
            continue
        longitude, latitude = to_wgs84.transform(float(attrs["x"]), float(attrs["y"]))
        attrs.setdefault("longitude", float(longitude))
        attrs.setdefault("latitude", float(latitude))
    edge_iterator = result.edges(keys=True, data=True) if result.is_multigraph() else (
        (u, v, None, attrs) for u, v, attrs in result.edges(data=True)
    )
    for u, v, _, attrs in edge_iterator:
        length = _edge_length(attrs, source_crs)
        if length is None:
            geometry = attrs.get("geometry")
            if geometry is not None and not source_crs.is_geographic:
                length = float(geometry.length) * float(source_crs.axis_info[0].unit_conversion_factor)
            elif all(name in result.nodes[u] for name in ("x", "y")) and all(
                name in result.nodes[v] for name in ("x", "y")
            ):
                x1, y1 = float(result.nodes[u]["x"]), float(result.nodes[u]["y"])
                x2, y2 = float(result.nodes[v]["x"]), float(result.nodes[v]["y"])
                if source_crs.is_geographic:
                    from pyproj import Geod

                    _, _, length = Geod(ellps="WGS84").inv(x1, y1, x2, y2)
                else:
                    length = math.hypot(x2 - x1, y2 - y1) * float(source_crs.axis_info[0].unit_conversion_factor)
        if length is not None and math.isfinite(length) and length >= 0:
            attrs["length_m"] = float(length)
            attrs.setdefault("length", float(length))
    return result


def project_graph(graph: nx.Graph, working_crs: str | CRS | None = None) -> nx.Graph:
    """Return an independent graph projected to an appropriate metric CRS."""
    source = normalize_graph(graph)
    crs = CRS.from_user_input(source.graph["crs"])
    if working_crs is None:
        if crs.is_projected:
            working_crs = crs
        else:
            points = [Point(float(attrs["x"]), float(attrs["y"])) for _, attrs in source.nodes(data=True) if "x" in attrs and "y" in attrs]
            if not points:
                raise ValueError("Cannot estimate a metric CRS without graph node coordinates.")
            working_crs = gpd.GeoSeries(points, crs=crs).estimate_utm_crs()
    target = CRS.from_user_input(working_crs)
    if not target.is_projected or not target.axis_info or not all(
        axis.unit_name.casefold() in {"metre", "meter"} for axis in target.axis_info[:2]
    ):
        raise ValueError(f"Working CRS must use projected metric units: {target}.")
    if crs.equals(target):
        projected = source
    else:
        projected = ox.project_graph(source, to_crs=target)
    # OSMnx's `length` is in metres for a projected graph; keep the canonical name.
    for _, _, attrs in projected.edges(data=True):
        length = _edge_length(attrs, target)
        if length is None and attrs.get("geometry") is not None:
            length = float(attrs["geometry"].length)
        if length is not None:
            attrs["length_m"] = length
    return projected


def network_metrics(graph: nx.Graph, mode: str) -> dict[str, Any]:
    """Summarize weak connectivity without treating missing tags as absence."""
    if graph.is_directed():
        components = [set(nodes) for nodes in nx.weakly_connected_components(graph)]
    else:
        components = [set(nodes) for nodes in nx.connected_components(graph)]
    components.sort(key=lambda nodes: (-len(nodes), min((_node_sort_key(n) for n in nodes), default=("", ""))))
    node_count = graph.number_of_nodes()
    largest = len(components[0]) if components else 0
    return {
        "mode": mode,
        "node_count": int(node_count),
        "edge_count": int(graph.number_of_edges()),
        "component_count": int(len(components)),
        "largest_component_nodes": int(largest),
        "largest_component_share": float(largest / node_count) if node_count else 0.0,
        "isolated_node_count": int(sum(1 for node, degree in graph.degree() if degree == 0)),
        "assumptions": ["Connected components use weak connectivity for directed OSM graphs."],
    }


def route_between(graph: nx.Graph, origin: Any, destination: Any) -> dict[str, Any]:
    """Calculate a network shortest path between graph node identifiers."""
    graph = normalize_graph(graph)
    if origin not in graph or destination not in graph:
        missing = [str(node) for node in (origin, destination) if node not in graph]
        raise RouteError(f"Unknown graph node(s): {', '.join(missing)}.")
    edges = graph.edges(data=True)
    if any(attrs.get("length_m") is None for _, _, attrs in edges):
        raise RouteError("Every routed graph edge must have a length in metres or coordinates from which to calculate it.")
    direct_distance: float | None = None
    if all(name in graph.nodes[origin] for name in ("x", "y")) and all(
        name in graph.nodes[destination] for name in ("x", "y")
    ) and graph.graph.get("crs"):
        crs = CRS.from_user_input(graph.graph["crs"])
        x1, y1 = float(graph.nodes[origin]["x"]), float(graph.nodes[origin]["y"])
        x2, y2 = float(graph.nodes[destination]["x"]), float(graph.nodes[destination]["y"])
        if crs.is_geographic:
            from pyproj import Geod

            _, _, direct_distance = Geod(ellps="WGS84").inv(x1, y1, x2, y2)
        elif crs.is_projected and all(axis.unit_name.casefold() in {"metre", "meter"} for axis in crs.axis_info[:2]):
            direct_distance = math.hypot(x2 - x1, y2 - y1)
    try:
        path = nx.shortest_path(graph, origin, destination, weight="length_m")
        distance = float(nx.shortest_path_length(graph, origin, destination, weight="length_m"))
    except nx.NetworkXNoPath:
        return {"status": "unreachable", "path": [], "distance_m": None, "direct_distance_m": direct_distance, "detour_ratio": None}
    detour_ratio = distance / direct_distance if direct_distance and direct_distance > 0 else None
    return {"status": "reachable", "path": path, "distance_m": distance, "direct_distance_m": direct_distance, "detour_ratio": detour_ratio}


def _nearest_nodes(graph: nx.Graph, points: Iterable[Point], source_crs: str = "EPSG:4326") -> tuple[list[Any], list[float]]:
    point_list = list(points)
    if not point_list:
        return [], []
    projected = gpd.GeoSeries(point_list, crs=source_crs).to_crs(graph.graph["crs"])
    ordered_nodes = sorted(graph.nodes, key=_node_sort_key)
    node_points = [Point(float(graph.nodes[node]["x"]), float(graph.nodes[node]["y"])) for node in ordered_nodes]
    if not node_points:
        return [], []
    # OSMnx's projected nearest_nodes path requires optional SciPy, which is not
    # part of this repository's locked dependencies. Shapely's STRtree is bundled
    # with the required Shapely 2.x dependency and provides the same metric lookup.
    tree = STRtree(node_points)
    nearest: list[Any] = []
    distances: list[float] = []
    for point in projected:
        matches = tree.query_nearest(point, all_matches=True)
        candidates = [int(index) for index in matches]
        selected = min(candidates, key=lambda index: _node_sort_key(ordered_nodes[index]))
        nearest.append(ordered_nodes[selected])
        distances.append(float(point.distance(node_points[selected])))
    return nearest, distances


def _feature_target_nodes(
    graph: nx.Graph,
    features: gpd.GeoDataFrame,
    *,
    snap_tolerance_m: float = 150.0,
) -> tuple[set[Any], list[str], int, list[Point]]:
    if features.empty:
        return set(), [], 0, []
    points: list[Point] = []
    ids: list[str] = []
    for row_index, row in features.iterrows():
        geometry = row.geometry
        if geometry is None or geometry.is_empty:
            continue
        point = geometry if isinstance(geometry, Point) else geometry.representative_point()
        points.append(point)
        osm_id = row.get("osm_id")
        ids.append(str(osm_id) if osm_id is not None else str(row_index))
    snapped, distances = _nearest_nodes(graph, points, source_crs=str(features.crs or "EPSG:4326"))
    accepted = [(node, osm_id, point) for node, osm_id, point, distance in zip(snapped, ids, points, distances) if distance <= snap_tolerance_m]
    accepted_points = list(gpd.GeoSeries([point for _, _, point in accepted], crs=features.crs or "EPSG:4326").to_crs(graph.graph["crs"]))
    return {node for node, _, _ in accepted}, [osm_id for _, osm_id, _ in accepted], len(points) - len(accepted), accepted_points


def _distances_to_targets(graph: nx.Graph, target_nodes: set[Any]) -> dict[Any, float]:
    if not target_nodes:
        return {}
    reverse = graph.reverse(copy=False) if graph.is_directed() else graph
    values = nx.multi_source_dijkstra_path_length(reverse, target_nodes, weight="length_m")
    return {node: float(distance) for node, distance in values.items()}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _provenance(data: OSMData, method: str) -> list[dict[str, Any]]:
    return [{
        "source": data.metadata["source"],
        "source_version": data.metadata["source_version"],
        "retrieved_at": data.metadata.get("retrieved_at"),
        "method": method,
        "crs": data.area.working_crs,
    }]


def _uncertainty(description: str, kind: str = "coverage_limitation") -> dict[str, Any]:
    return {"kind": kind, "description": description, "interval": None, "confidence": None}


def _indicator(identifier: str, label: str, value: Any, unit: str, provenance: list[dict[str, Any]], uncertainty: dict[str, Any]) -> dict[str, Any]:
    status = "unknown" if value is None else "calculated"
    return {"id": identifier, "label": label, "value": value, "unit": unit, "status": status, "provenance": provenance, "uncertainty": uncertainty}


def _stable_issue_id(area_id: str, issue_type: str, suffix: str) -> str:
    safe = hashlib.sha256(f"{area_id}|{issue_type}|{suffix}".encode("utf-8")).hexdigest()[:14]
    return f"issue_{safe}"


def _node_point(node_attrs: dict[str, Any], graph_crs: str) -> Point | None:
    if "x" not in node_attrs or "y" not in node_attrs:
        return None
    return Point(float(node_attrs["x"]), float(node_attrs["y"]))


def _issue(
    *,
    issue_id: str,
    issue_type: str,
    severity: str,
    geometry: Any,
    metrics: dict[str, Any],
    evidence: list[dict[str, Any]],
    coverage: dict[str, Any],
    provenance: list[dict[str, Any]],
    crs: str,
    description: str,
) -> dict[str, Any]:
    return {
        "id": issue_id,
        "type": issue_type,
        "severity": severity,
        "description": description,
        "geometry": geojson_geometry(geometry, crs),
        "metrics": metrics,
        "evidence": evidence,
        "data_coverage": coverage,
        "provenance": provenance,
        "uncertainty": _uncertainty("OSM mapping and tags may be incomplete; this issue describes the downloaded snapshot only."),
    }


def _network_layer(graph: nx.Graph, area: StudyArea) -> gpd.GeoDataFrame:
    edges = ox.graph_to_gdfs(graph, nodes=False, edges=True, fill_edge_geometry=True)
    edges = edges.reset_index()
    if "length_m" not in edges and "length" in edges:
        edges["length_m"] = edges["length"].astype(float)
    edges = edges.to_crs("EPSG:4326")
    return gpd.clip(edges, area.polygon).reset_index(drop=True) if not edges.empty else edges


def _nodes_inside_area(graph: nx.Graph, area: StudyArea) -> set[Any]:
    polygon = gpd.GeoSeries([area.polygon], crs="EPSG:4326").to_crs(area.working_crs).iloc[0]
    inside: set[Any] = set()
    for node, attrs in graph.nodes(data=True):
        point = _node_point(attrs, area.working_crs)
        if point is not None and polygon.covers(point):
            inside.add(node)
    return inside


def analyze_snapshot(
    data: OSMData,
    *,
    access_threshold_minutes: float = DEFAULT_ACCESS_THRESHOLD_MINUTES,
    walking_speed_mps: float = WALK_SPEED_MPS,
    cycling_speed_mps: float = BIKE_SPEED_MPS,
    poi_snap_tolerance_m: float = 150.0,
    detour_ratio_threshold: float = 2.0,
) -> dict[str, Any]:
    """Produce JSON-ready indicators, explainable issues, and map GeoJSON."""
    if access_threshold_minutes <= 0 or walking_speed_mps <= 0 or cycling_speed_mps <= 0 or detour_ratio_threshold <= 1:
        raise ValueError("Travel-time thresholds and speeds must be positive; detour ratio threshold must be greater than 1.")
    area = data.area
    metrics_by_mode: dict[str, dict[str, Any]] = {}
    metric_graphs: dict[str, nx.Graph] = {}
    interior_nodes_by_mode: dict[str, set[Any]] = {}
    indicators: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    heatmaps: dict[str, dict[str, Any]] = {}
    warnings = list(data.warnings)
    provenance = _provenance(data, "OSMnx mode-specific street graph and NetworkX graph analysis")

    for mode, graph in data.graphs.items():
        projected = project_graph(graph, area.working_crs)
        metric_graphs[mode] = projected
        summary = network_metrics(projected, mode)
        interior_nodes = _nodes_inside_area(projected, area)
        interior_nodes_by_mode[mode] = interior_nodes
        summary["study_area_node_count"] = len(interior_nodes)
        summary["graph_node_count_including_boundary_connectors"] = projected.number_of_nodes()
        metrics_by_mode[mode] = summary
        indicators.extend([
            _indicator(f"{mode}_network_nodes", f"Nodes in retrieved {mode} graph, including boundary connectors", summary["node_count"], "node", provenance, _uncertainty("Graph node totals may include one-edge boundary connectors outside the selected polygon.")),
            _indicator(f"{mode}_study_area_network_nodes", f"Mapped {mode} network nodes inside the study area", summary["study_area_node_count"], "node", provenance, _uncertainty("Counts mapped graph nodes inside the polygon; it is not a population count.")),
            _indicator(f"{mode}_network_components", f"Weakly connected {mode} graph components", summary["component_count"], "component", provenance, _uncertainty("Components include retained boundary connectors and may reflect OSM coverage gaps.")),
            _indicator(f"{mode}_largest_component_share", f"Share of retrieved {mode} graph nodes in the largest component", summary["largest_component_share"], "ratio", provenance, _uncertainty("This ratio covers retrieved graph nodes, including boundary connectors, not residents or trips.")),
        ])
        components = [set(part) for part in (nx.weakly_connected_components(projected) if projected.is_directed() else nx.connected_components(projected))]
        components.sort(key=lambda nodes: (-len(nodes), min((_node_sort_key(n) for n in nodes), default=("", ""))))
        for component in components[1:]:
            in_area_component = component & interior_nodes
            if not in_area_component:
                continue
            points = [_node_point(projected.nodes[node], area.working_crs) for node in sorted(in_area_component, key=_node_sort_key)]
            points = [point for point in points if point is not None]
            if not points:
                continue
            geometry = MultiPoint(points[:MAX_ISSUE_GEOMETRY_POINTS]).centroid
            issue_type = f"disconnected_{mode}_component"
            issues.append(_issue(
                issue_id=_stable_issue_id(area.area_id, issue_type, str(min(component, key=_node_sort_key))),
                issue_type=issue_type,
                severity="high" if len(in_area_component) == 1 else "medium",
                geometry=geometry,
                metrics={"component_node_count": len(component), "component_node_count_in_study_area": len(in_area_component), "graph_component_count": len(components), "largest_component_share": summary["largest_component_share"], "units": {"component_node_count": "node", "component_node_count_in_study_area": "node", "graph_component_count": "component", "largest_component_share": "ratio"}},
                evidence=[{"source": "OpenStreetMap", "osm_node_ids": [str(node) for node in sorted(component, key=_node_sort_key)[:50]]}],
                coverage={"mapped_network_nodes": summary["node_count"], "study_area_network_nodes": len(interior_nodes), "component_node_count_in_study_area": len(in_area_component)},
                provenance=provenance,
                crs=area.working_crs,
                description=f"This {mode} network component has no route to the largest mapped component in the downloaded graph.",
            ))

    category_modes = {
        "walk": ("schools", "healthcare", "services", "public_transport", "green_space"),
        "bike": ("schools", "healthcare", "services", "public_transport", "green_space"),
    }
    speeds = {"walk": walking_speed_mps, "bike": cycling_speed_mps}
    for mode, categories in category_modes.items():
        graph = metric_graphs.get(mode)
        if graph is None:
            continue
        threshold_distance = access_threshold_minutes * 60.0 * speeds[mode]
        for category in categories:
            features = data.layers.get(category)
            if features is None or features.empty:
                availability = data.layer_availability.get(category, {}).get("status", "unknown")
                indicators.append(_indicator(
                    f"{mode}_access_{category}_within_{int(access_threshold_minutes)}_min",
                    f"Mapped {mode} network nodes within {access_threshold_minutes:g} minutes of {category}",
                    None,
                    "node",
                    provenance,
                    _uncertainty(f"No mapped {category} targets were returned (layer status: {availability}); accessibility is unknown, not zero.", "missing_data"),
                ))
                indicators.append(_indicator(
                    f"{mode}_median_detour_ratio_to_{category}",
                    f"Median route detour ratio to {category}",
                    None,
                    "ratio",
                    provenance,
                    _uncertainty(f"No mapped {category} targets were returned (layer status: {availability}); detour ratio is unknown.", "missing_data"),
                ))
                continue
            target_nodes, target_osm_ids, excluded_count, target_points = _feature_target_nodes(graph, features, snap_tolerance_m=poi_snap_tolerance_m)
            identifier = f"{mode}_access_{category}_within_{int(access_threshold_minutes)}_min"
            if not target_nodes:
                indicators.append(_indicator(identifier, f"Mapped {mode} network nodes within {access_threshold_minutes:g} minutes of {category}", None, "node", provenance, _uncertainty(f"No {category} features snapped within {poi_snap_tolerance_m:g} m of the graph; accessibility is unknown.", "missing_data")))
                indicators.append(_indicator(f"{identifier}_share", f"Share of mapped {mode} nodes within threshold of {category}", None, "ratio", provenance, _uncertainty("No snap-eligible target features were available.", "missing_data")))
                indicators.append(_indicator(f"{mode}_median_detour_ratio_to_{category}", f"Median route detour ratio to {category}", None, "ratio", provenance, _uncertainty("No snap-eligible target features were available.", "missing_data")))
                continue
            distances = _distances_to_targets(graph, target_nodes)
            within = [node for node, distance in distances.items() if distance <= threshold_distance]
            area_nodes = interior_nodes_by_mode[mode]
            total_nodes = len(area_nodes)
            if total_nodes == 0:
                indicators.append(_indicator(identifier, f"Mapped {mode} network nodes within {access_threshold_minutes:g} minutes of {category}", None, "node", provenance, _uncertainty("No retrieved graph nodes lie inside the selected polygon.", "missing_data")))
                indicators.append(_indicator(f"{identifier}_share", f"Share of mapped {mode} nodes within threshold of {category}", None, "ratio", provenance, _uncertainty("No retrieved graph nodes lie inside the selected polygon.", "missing_data")))
                indicators.append(_indicator(f"{mode}_median_detour_ratio_to_{category}", f"Median route detour ratio to {category}", None, "ratio", provenance, _uncertainty("No retrieved graph nodes lie inside the selected polygon.", "missing_data")))
                continue
            within = [node for node in within if node in area_nodes]
            outside_count = total_nodes - len(within)
            unreachable_count = sum(1 for node in area_nodes if node not in distances)
            within_share = len(within) / total_nodes if total_nodes else 0.0
            indicators.append(_indicator(
                identifier,
                f"Mapped {mode} network nodes within {access_threshold_minutes:g} minutes of {category}",
                len(within),
                "node",
                _provenance(data, f"NetworkX multi-source Dijkstra; {speeds[mode]:g} m/s assumed; {access_threshold_minutes:g} minute threshold"),
                _uncertainty("Node coverage is not population-weighted; OSM POI and network coverage may be incomplete."),
            ))
            indicators.append(_indicator(
                f"{identifier}_share",
                f"Share of mapped {mode} nodes within threshold of {category}",
                within_share,
                "ratio",
                _provenance(data, f"NetworkX multi-source Dijkstra; {speeds[mode]:g} m/s assumed; {access_threshold_minutes:g} minute threshold"),
                _uncertainty("Denominator includes mapped graph nodes only; it is not a population access rate."),
            ))
            direct_tree = STRtree(target_points)
            detour_rows: list[tuple[float, Any, float, float]] = []
            for node in sorted(area_nodes, key=_node_sort_key):
                network_distance = distances.get(node)
                if network_distance is None:
                    continue
                node_point = Point(float(graph.nodes[node]["x"]), float(graph.nodes[node]["y"]))
                nearest_index = int(direct_tree.nearest(node_point))
                direct_distance = float(node_point.distance(target_points[nearest_index]))
                if direct_distance > 1.0:
                    detour_rows.append((network_distance / direct_distance, node, network_distance, direct_distance))
            detour_values = [row[0] for row in detour_rows]
            detour_by_node = {node: ratio for ratio, node, _, _ in detour_rows}
            median_detour = statistics.median(detour_values) if detour_values else None
            indicators.append(_indicator(
                f"{mode}_median_detour_ratio_to_{category}",
                f"Median route detour ratio to {category}",
                median_detour,
                "ratio",
                _provenance(data, "NetworkX shortest network distance divided by straight-line distance to the nearest mapped feature geometry"),
                _uncertainty("Ratios cover reachable graph nodes and mapped target geometry only; straight-line distance is a reference, not a feasible route."),
            ))
            detour_exceedances = [row for row in detour_rows if row[0] > detour_ratio_threshold]
            if detour_exceedances:
                exceedance_share = len(detour_exceedances) / total_nodes if total_nodes else 0.0
                severity = "high" if exceedance_share >= 0.25 else "medium" if exceedance_share >= 0.10 else "low"
                detour_points = [_node_point(graph.nodes[node], area.working_crs) for _, node, _, _ in detour_exceedances[:MAX_ISSUE_GEOMETRY_POINTS]]
                detour_points = [point for point in detour_points if point is not None]
                if detour_points:
                    issues.append(_issue(
                        issue_id=_stable_issue_id(area.area_id, f"{mode}_excessive_detour", category),
                        issue_type=f"{mode}_excessive_detour_to_{category}",
                        severity=severity,
                        geometry=MultiPoint(detour_points).centroid,
                        metrics={"network_nodes_over_detour_threshold": len(detour_exceedances), "study_area_network_nodes": total_nodes, "threshold_ratio": detour_ratio_threshold, "median_detour_ratio": median_detour, "maximum_detour_ratio": max(row[0] for row in detour_exceedances), "units": {"network_nodes_over_detour_threshold": "node", "study_area_network_nodes": "node", "threshold_ratio": "ratio", "median_detour_ratio": "ratio", "maximum_detour_ratio": "ratio"}},
                        evidence=[{"source": "OpenStreetMap", "target_layer": category, "target_osm_ids": sorted(set(target_osm_ids))[:50], "method": "network distance divided by straight-line distance to nearest mapped feature geometry"}],
                        coverage={"target_feature_count": int(len(features)), "targets_snapped_to_graph": len(target_nodes), "mapped_network_nodes": total_nodes},
                        provenance=_provenance(data, f"NetworkX weighted shortest path; issue threshold ratio > {detour_ratio_threshold:g}"),
                        crs=area.working_crs,
                        description=f"The calculated network route exceeds {detour_ratio_threshold:g} times the straight-line reference to a mapped {category} feature; this is a screening signal, not a construction recommendation.",
                    ))

            heatmap_rows: list[tuple[float, Any, float, float | None]] = []
            for node in sorted(area_nodes, key=_node_sort_key):
                distance = distances.get(node, math.inf)
                if distance > threshold_distance:
                    detour = detour_by_node.get(node)
                    heatmap_rows.append((distance, node, distance / speeds[mode] if math.isfinite(distance) else math.inf, detour))
            heatmap_rows.sort(key=lambda item: (-item[0], _node_sort_key(item[1])))
            selected = heatmap_rows[:MAX_HEATMAP_FEATURES]
            heatmap_features: list[dict[str, Any]] = []
            for distance, node, minutes, detour in selected:
                point = _node_point(graph.nodes[node], area.working_crs)
                if point is None:
                    continue
                heatmap_features.append({
                    "type": "Feature",
                    "id": f"{mode}:{category}:{node}",
                    "geometry": geojson_geometry(point, area.working_crs),
                    "properties": {
                        "network_node_id": str(node),
                        "target_layer": category,
                        "network_distance_m": distance if math.isfinite(distance) else None,
                        "estimated_travel_time_min": minutes / 60 if math.isfinite(minutes) else None,
                        "detour_ratio": detour,
                        "reachable": math.isfinite(distance),
                        "status": "calculated" if math.isfinite(distance) else "unknown",
                    },
                })
            heatmaps[f"{mode}_{category}"] = {"type": "FeatureCollection", "features": heatmap_features}

            if outside_count:
                bad_nodes = [node for _, node, _, _ in heatmap_rows]
                bad_points = [_node_point(graph.nodes[node], area.working_crs) for node in bad_nodes[:MAX_ISSUE_GEOMETRY_POINTS]]
                bad_points = [point for point in bad_points if point is not None]
                if bad_points:
                    unreachable_share = unreachable_count / total_nodes if total_nodes else 0.0
                    outside_share = outside_count / total_nodes if total_nodes else 0.0
                    if unreachable_share >= 0.25:
                        severity = "high"
                    elif unreachable_count > 0 or outside_share >= 0.25:
                        severity = "medium"
                    else:
                        severity = "low"
                    issues.append(_issue(
                        issue_id=_stable_issue_id(area.area_id, f"{mode}_poor_access", category),
                        issue_type=f"{mode}_poor_access_to_{category}",
                        severity=severity,
                        geometry=MultiPoint(bad_points).centroid,
                        metrics={
                            "network_nodes_outside_threshold": outside_count,
                            "network_nodes_unreachable": unreachable_count,
                            "network_node_count": total_nodes,
                            "threshold_min": access_threshold_minutes,
                            "assumed_speed_m_s": speeds[mode],
                            "units": {"network_nodes_outside_threshold": "node", "network_nodes_unreachable": "node", "network_node_count": "node", "threshold_min": "minute", "assumed_speed_m_s": "m/s"},
                        },
                        evidence=[{"source": "OpenStreetMap", "target_layer": category, "target_osm_ids": sorted(set(target_osm_ids))[:50], "method": "shortest network distance to nearest snap-eligible mapped target"}],
                        coverage={"target_feature_count": int(len(features)), "targets_snapped_to_graph": len(target_nodes), "targets_excluded_beyond_snap_tolerance": excluded_count, "mapped_network_nodes": total_nodes, "heatmap_feature_count": len(heatmap_features)},
                        provenance=_provenance(data, f"NetworkX multi-source Dijkstra; {speeds[mode]:g} m/s assumed; {access_threshold_minutes:g} minute threshold"),
                        crs=area.working_crs,
                        description=f"Some mapped {mode} network nodes are beyond the configured access threshold to mapped {category} features; no population impact is inferred.",
                    ))
            if len(heatmap_rows) > MAX_HEATMAP_FEATURES:
                warnings.append(f"Heatmap {mode}_{category} is capped at {MAX_HEATMAP_FEATURES} features; indicator counts use all nodes.")

    indicators.append(_indicator(
        "population_accessibility",
        "Population accessibility to mapped services",
        None,
        "person",
        [],
        _uncertainty("No population or address-level demand dataset is included in this OSM snapshot.", "missing_data"),
    ))

    layer_geojson = {
        name: feature_collection(gpd.clip(frame.to_crs("EPSG:4326"), area.polygon).reset_index(drop=True) if not frame.empty else frame)
        for name, frame in data.layers.items()
    }
    network_geojson: dict[str, Any] = {}
    for mode, graph in data.graphs.items():
        edges = _network_layer(graph, area)
        network_geojson[mode] = feature_collection(edges)

    snapshot_key = json.dumps({"area": area.extent, "retrieved_at": data.metadata.get("retrieved_at"), "graphs": {mode: [graph.number_of_nodes(), graph.number_of_edges()] for mode, graph in data.graphs.items()}}, sort_keys=True)
    analysis_id = "an_" + hashlib.sha256(snapshot_key.encode("utf-8")).hexdigest()[:20]
    return {
        "analysis_id": analysis_id,
        "area": {
            "city_id": area.city_id,
            "area_id": area.area_id,
            "boundary": area.geojson,
            "boundary_source": area.boundary_source,
            "crs": "EPSG:4326",
            "working_crs": area.working_crs,
        },
        "created_at": _timestamp(),
        "indicators": indicators,
        "issues": issues,
        "issue_geojson": {"type": "FeatureCollection", "features": [
            {"type": "Feature", "id": item["id"], "geometry": item["geometry"], "properties": {key: value for key, value in item.items() if key != "geometry"}}
            for item in issues
        ]},
        "heatmaps": heatmaps,
        "layer_availability": data.layer_availability,
        "layers": layer_geojson,
        "networks": network_geojson,
        "network_metrics": metrics_by_mode,
        "provenance": data.metadata,
        "uncertainty": _uncertainty("OSM completeness varies by place and tag; this output is a snapshot, not a complete inventory."),
        "warnings": warnings + ["OpenStreetMap data copyright OpenStreetMap contributors; attribution and ODbL terms apply.", "Network-node accessibility is not population-weighted; no traffic delay or congestion is inferred."],
    }


def analyze_area(area: Any, **options: Any) -> dict[str, Any]:
    """Acquire real OSM data for a bounded area and analyze its networks."""
    acquisition_keys = {"modes", "cache_dir", "use_cache", "force_refresh", "overpass_url", "max_area_km2", "max_extent_km"}
    acquisition_options = {key: options.pop(key) for key in list(options) if key in acquisition_keys}
    from .geo import acquire_osm_data

    data = acquire_osm_data(area, **acquisition_options)
    return analyze_snapshot(data, **options)
