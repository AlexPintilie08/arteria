"""Isolated, measurable pedestrian network intervention scenarios."""

from __future__ import annotations

import hashlib
import math
from typing import Any, Iterable

import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import LineString, Point

from .analysis import _nearest_nodes, project_graph, route_between
from .geo import OSMData, geojson_geometry


MAX_CONNECTION_LENGTH_M = 1_000.0
MAX_NODE_SNAP_M = 250.0
WALK_SPEED_MPS = 1.3


class InterventionError(ValueError):
    """Raised for unsupported or geographically invalid interventions."""


def _coordinate_point(value: Any, field: str) -> Point:
    if isinstance(value, Point):
        point = value
    elif isinstance(value, dict) and value.get("type") == "Point":
        coords = value.get("coordinates", ())
        if len(coords) != 2:
            raise InterventionError(f"{field} must be a GeoJSON Point with [longitude, latitude].")
        point = Point(float(coords[0]), float(coords[1]))
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        point = Point(float(value[0]), float(value[1]))
    else:
        raise InterventionError(f"{field} must be a Point or [longitude, latitude] in EPSG:4326.")
    if point.is_empty or not (-180 <= point.x <= 180 and -90 <= point.y <= 90):
        raise InterventionError(f"{field} coordinates are outside EPSG:4326 bounds.")
    return point


def _snap_to_graph(graph: nx.Graph, point: Point, area: OSMData, field: str, tolerance_m: float) -> tuple[Any, float]:
    if not area.area.polygon.covers(point):
        raise InterventionError(f"{field} must lie inside the selected study area.")
    nodes, distances = _nearest_nodes(graph, [point])
    if not nodes:
        raise InterventionError(f"{field} cannot be matched to a mapped walking network node.")
    node, distance = nodes[0], distances[0]
    if distance > tolerance_m:
        raise InterventionError(f"{field} is {distance:.1f} m from the nearest walking node, beyond the {tolerance_m:g} m snap limit.")
    return node, distance


def _edge_values(graph: nx.Graph, u: Any, v: Any) -> list[dict[str, Any]]:
    values = graph.get_edge_data(u, v)
    if values is None:
        return []
    if graph.is_multigraph():
        return list(values.values())
    return [values]


def _connection_id(u: Any, v: Any, length_m: float) -> str:
    endpoints = sorted((f"{type(u).__name__}:{u}", f"{type(v).__name__}:{v}"))
    seed = f"{endpoints[0]}|{endpoints[1]}|{length_m:.1f}"
    return "arteria:" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _has_connection(graph: nx.Graph, connection_id: str) -> bool:
    edges = graph.edges(keys=True, data=True) if graph.is_multigraph() else (
        (u, v, None, attrs) for u, v, attrs in graph.edges(data=True)
    )
    return any(attrs.get("arteria_virtual_id") == connection_id for _, _, _, attrs in edges)


def _remove_connection(graph: nx.Graph, connection_id: str) -> int:
    edges = graph.edges(keys=True, data=True) if graph.is_multigraph() else (
        (u, v, None, attrs) for u, v, attrs in graph.edges(data=True)
    )
    to_remove = [(u, v, key) for u, v, key, attrs in list(edges) if attrs.get("arteria_virtual_id") == connection_id]
    for u, v, key in to_remove:
        if graph.is_multigraph():
            graph.remove_edge(u, v, key)
        else:
            graph.remove_edge(u, v)
    return len(to_remove)


def _add_connection(
    graph: nx.Graph,
    data: OSMData,
    start: Point,
    end: Point,
    *,
    max_snap_distance_m: float,
    requested_id: str | None = None,
) -> dict[str, Any]:
    start_node, start_snap_m = _snap_to_graph(graph, start, data, "start", max_snap_distance_m)
    end_node, end_snap_m = _snap_to_graph(graph, end, data, "end", max_snap_distance_m)
    if start_node == end_node:
        raise InterventionError("Intervention endpoints snap to the same graph node.")
    start_attrs, end_attrs = graph.nodes[start_node], graph.nodes[end_node]
    line = LineString([(float(start_attrs["x"]), float(start_attrs["y"])), (float(end_attrs["x"]), float(end_attrs["y"]))])
    if not data.area.polygon.covers(gpd.GeoSeries([line], crs=graph.graph["crs"]).to_crs("EPSG:4326").iloc[0]):
        raise InterventionError("The hypothetical connection geometry must remain inside the selected area.")
    length_m = float(line.length)
    if not math.isfinite(length_m) or length_m <= 0 or length_m > MAX_CONNECTION_LENGTH_M:
        raise InterventionError(f"Connection length must be greater than zero and no longer than {MAX_CONNECTION_LENGTH_M:g} m.")
    derived_id = _connection_id(start_node, end_node, length_m)
    if requested_id is not None and requested_id != derived_id:
        raise InterventionError("connection_id does not match the stable identifier derived from the snapped endpoints and length.")
    connection_id = derived_id
    edge_common = {
        "arteria_virtual_id": connection_id,
        "source": "hypothetical_intervention",
        "highway": "footway",
        "length": length_m,
        "length_m": length_m,
        "estimated_walk_time_s": length_m / WALK_SPEED_MPS,
        "geometry": line,
        "assumption": "Straight-line hypothetical link; feasibility, safety, ownership, grade, and legal approval are not assessed.",
    }
    if graph.is_multigraph():
        graph.add_edge(start_node, end_node, key=f"{connection_id}:forward", **edge_common)
        graph.add_edge(end_node, start_node, key=f"{connection_id}:reverse", **edge_common)
    else:
        graph.add_edge(start_node, end_node, **edge_common)
        if graph.is_directed():
            graph.add_edge(end_node, start_node, **edge_common)
    return {
        "connection_id": connection_id,
        "start_node_id": str(start_node),
        "end_node_id": str(end_node),
        "start_snap_distance_m": start_snap_m,
        "end_snap_distance_m": end_snap_m,
        "connection_length_m": length_m,
        "estimated_walk_time_s": length_m / WALK_SPEED_MPS,
        "geometry": line,
    }


def _apply_interventions(
    graph: nx.Graph,
    data: OSMData,
    interventions: Iterable[dict[str, Any]],
    *,
    max_snap_distance_m: float,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, intervention in enumerate(interventions):
        kind = intervention.get("type")
        if kind == "add_pedestrian_connection":
            start = _coordinate_point(intervention.get("start"), f"interventions[{index}].start")
            end = _coordinate_point(intervention.get("end"), f"interventions[{index}].end")
            result = _add_connection(
                graph,
                data,
                start,
                end,
                max_snap_distance_m=max_snap_distance_m,
                requested_id=intervention.get("connection_id"),
            )
            result.update({"type": kind, "status": "applied"})
            results.append(result)
            continue
        if kind == "set_connection_enabled":
            enabled = intervention.get("enabled")
            if not isinstance(enabled, bool):
                raise InterventionError(f"interventions[{index}].enabled must be a boolean.")
            connection_id = intervention.get("connection_id")
            if not connection_id and "start" in intervention and "end" in intervention:
                start = _coordinate_point(intervention["start"], f"interventions[{index}].start")
                end = _coordinate_point(intervention["end"], f"interventions[{index}].end")
                descriptor = _add_connection(
                    graph if enabled else graph.copy(), data, start, end,
                    max_snap_distance_m=max_snap_distance_m,
                )
                connection_id = descriptor["connection_id"]
                if enabled:
                    descriptor.update({"status": "enabled", "type": kind})
                    results.append(descriptor)
                    continue
                # The temporary copy was only used to derive/validate the modeled edge.
                descriptor["removed_directed_edges"] = _remove_connection(graph, connection_id)
                descriptor["status"] = "disabled" if descriptor["removed_directed_edges"] else "already_disabled"
                descriptor["type"] = kind
                results.append(descriptor)
                continue
            if not isinstance(connection_id, str) or not connection_id.startswith("arteria:"):
                raise InterventionError(f"interventions[{index}] must identify a modeled ARTERIA pedestrian connection.")
            present = _has_connection(graph, connection_id)
            if not present and not enabled and not ("start" in intervention and "end" in intervention):
                raise InterventionError("Disabling a connection absent from the baseline requires its start and end coordinates.")
            if enabled and not present:
                if "start" not in intervention or "end" not in intervention:
                    raise InterventionError("Enabling a connection not present in the baseline requires its start and end coordinates.")
                start = _coordinate_point(intervention["start"], f"interventions[{index}].start")
                end = _coordinate_point(intervention["end"], f"interventions[{index}].end")
                descriptor = _add_connection(graph, data, start, end, max_snap_distance_m=max_snap_distance_m, requested_id=connection_id)
                results.append({**descriptor, "type": kind, "status": "enabled"})
            elif enabled:
                results.append({"type": kind, "connection_id": connection_id, "status": "already_enabled"})
            else:
                removed = _remove_connection(graph, connection_id)
                results.append({"type": kind, "connection_id": connection_id, "status": "disabled" if removed else "already_disabled", "removed_directed_edges": removed})
            continue
        raise InterventionError(f"Unsupported pedestrian intervention type: {kind!r}.")
    return results


def _route_geometry(graph: nx.Graph, path: list[Any]) -> LineString | Point | None:
    if not path:
        return None
    if len(path) == 1:
        attrs = graph.nodes[path[0]]
        return Point(float(attrs["x"]), float(attrs["y"]))
    coordinates: list[tuple[float, float]] = []
    for u, v in zip(path, path[1:]):
        edges = _edge_values(graph, u, v)
        if not edges:
            continue
        attrs = min(edges, key=lambda item: float(item.get("length_m", item.get("length", math.inf))))
        geometry = attrs.get("geometry")
        if geometry is None or geometry.is_empty:
            segment = LineString([(graph.nodes[u]["x"], graph.nodes[u]["y"]), (graph.nodes[v]["x"], graph.nodes[v]["y"])])
        else:
            segment = geometry
        coords = list(segment.coords)
        start_xy = (float(graph.nodes[u]["x"]), float(graph.nodes[u]["y"]))
        if math.dist(coords[-1], start_xy) < math.dist(coords[0], start_xy):
            coords.reverse()
        if coordinates and coordinates[-1] == coords[0]:
            coordinates.extend(coords[1:])
        else:
            coordinates.extend(coords)
    return LineString(coordinates) if len(coordinates) >= 2 else None


def _route_result(graph: nx.Graph, origin: Any, destination: Any, speed_mps: float) -> dict[str, Any]:
    route = route_between(graph, origin, destination)
    if route["status"] == "unreachable":
        return {**route, "estimated_walk_time_s": None, "geometry": None}
    return {
        **route,
        "estimated_walk_time_s": route["distance_m"] / speed_mps,
        "geometry": _route_geometry(graph, route["path"]),
    }


def evaluate_scenario(
    data: OSMData,
    interventions: Iterable[dict[str, Any]],
    *,
    origin: Any,
    destination: Any,
    max_snap_distance_m: float = 50.0,
    walking_speed_mps: float = WALK_SPEED_MPS,
) -> dict[str, Any]:
    """Apply pedestrian interventions on an isolated graph and compare routes."""
    if "walk" not in data.graphs:
        raise InterventionError("A walking baseline network is required.")
    if not (0 < max_snap_distance_m <= MAX_NODE_SNAP_M):
        raise InterventionError(f"Node snap tolerance must be in (0, {MAX_NODE_SNAP_M:g}] m.")
    if walking_speed_mps <= 0:
        raise InterventionError("Walking speed must be positive.")
    baseline_graph = project_graph(data.graphs["walk"], data.area.working_crs)
    scenario_graph = baseline_graph.copy()
    applied = _apply_interventions(scenario_graph, data, interventions, max_snap_distance_m=max_snap_distance_m)

    origin_point = _coordinate_point(origin, "origin")
    destination_point = _coordinate_point(destination, "destination")
    origin_node, origin_snap = _snap_to_graph(baseline_graph, origin_point, data, "origin", max_snap_distance_m)
    destination_node, destination_snap = _snap_to_graph(baseline_graph, destination_point, data, "destination", max_snap_distance_m)
    before = _route_result(baseline_graph, origin_node, destination_node, walking_speed_mps)
    after = _route_result(scenario_graph, origin_node, destination_node, walking_speed_mps)
    if before["status"] == "reachable" and after["status"] == "reachable":
        delta = after["distance_m"] - before["distance_m"]
        outcome = "improved" if delta < -0.01 else "regressed" if delta > 0.01 else "unchanged"
    elif before["status"] == "unreachable" and after["status"] == "reachable":
        delta, outcome = None, "became_reachable"
    elif before["status"] == "reachable" and after["status"] == "unreachable":
        delta, outcome = None, "became_unreachable"
    else:
        delta, outcome = None, "unreachable_in_both"

    def route_payload(route: dict[str, Any]) -> dict[str, Any]:
        geometry = route.pop("geometry")
        return {
            "status": route["status"],
            "network_distance_m": route["distance_m"],
            "direct_distance_m": route["direct_distance_m"],
            "detour_ratio": route["detour_ratio"],
            "estimated_walk_time_s": route["estimated_walk_time_s"],
            "path_node_ids": [str(node) for node in route["path"]],
            "geometry": geojson_geometry(geometry, data.area.working_crs) if geometry is not None else None,
        }

    before_json = route_payload(before)
    after_json = route_payload(after)
    return {
        "scenario_id": "sc_" + hashlib.sha256(repr([(item.get("type"), item.get("connection_id"), item.get("status")) for item in applied]).encode("utf-8")).hexdigest()[:20],
        "area_id": data.area.area_id,
        "mode": "walk",
        "baseline": before_json,
        "scenario": after_json,
        "comparison": {
            "outcome": outcome,
            "distance_delta_m": delta,
            "time_delta_s": (after_json["estimated_walk_time_s"] - before_json["estimated_walk_time_s"]) if before_json["estimated_walk_time_s"] is not None and after_json["estimated_walk_time_s"] is not None else None,
            "improvement_percent": None,
            "assumption": f"Estimated walking time uses a constant {walking_speed_mps:g} m/s speed; no crossings, slope, delays, or personal mobility differences are modeled.",
        },
        "interventions": [{key: value for key, value in item.items() if key != "geometry"} | ({"geometry": geojson_geometry(item["geometry"], data.area.working_crs)} if item.get("geometry") is not None else {}) for item in applied],
        "snap": {"origin_node_id": str(origin_node), "origin_distance_m": origin_snap, "destination_node_id": str(destination_node), "destination_distance_m": destination_snap},
        "provenance": {"source": "OpenStreetMap", "retrieved_at": data.metadata.get("retrieved_at"), "working_crs": data.area.working_crs, "method": "NetworkX weighted shortest path on baseline and isolated scenario graph"},
        "warnings": ["Interventions are hypothetical network edits; physical feasibility, accessibility standards, safety, land ownership, and legal approvals are not verified.", "The original baseline graph is never modified.", "No vehicle traffic or congestion is inferred."],
    }


def evaluate_pedestrian_connection(
    data: OSMData,
    start: Any,
    end: Any,
    *,
    origin: Any | None = None,
    destination: Any | None = None,
    max_snap_distance_m: float = 50.0,
    walking_speed_mps: float = WALK_SPEED_MPS,
) -> dict[str, Any]:
    """Convenience API for one hypothetical pedestrian connection."""
    start_point = _coordinate_point(start, "start")
    end_point = _coordinate_point(end, "end")
    return evaluate_scenario(
        data,
        [{"type": "add_pedestrian_connection", "start": [start_point.x, start_point.y], "end": [end_point.x, end_point.y]}],
        origin=origin if origin is not None else [start_point.x, start_point.y],
        destination=destination if destination is not None else [end_point.x, end_point.y],
        max_snap_distance_m=max_snap_distance_m,
        walking_speed_mps=walking_speed_mps,
    )
