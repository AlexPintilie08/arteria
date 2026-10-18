"""Bounded OSM driving-graph conversion and optional headless SUMO execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
from pyproj import CRS, Transformer
from shapely import transform as transform_geometry
from shapely.geometry import LineString

from .analysis import project_graph
from .demo import DEFAULT_AREA
from .geo import LAYER_TAGS, OSMData, _area_key, _source_area_geometry_hash, normalize_area
from .sumo_support import SumoInstallation, discover_sumo


DEFAULT_MAX_NODES = 15_000
DEFAULT_MAX_EDGES = 50_000
MAX_VEHICLES = 200
MAX_DURATION_SECONDS = 600.0
MAX_EXECUTION_TIMEOUT_SECONDS = 180.0
DEFAULT_SPEED_MPS = 13.9
DEFAULT_LANES_PER_DIRECTION = 1


class SumoPreparationError(RuntimeError):
    """Raised when a bounded driving graph cannot be represented for SUMO."""


def _stable_sort(value: Any) -> str:
    return f"{type(value).__name__}:{value}"


def _stable_id(prefix: str, *parts: Any) -> str:
    identity = "\0".join(_stable_sort(part) for part in parts)
    return prefix + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _parse_speed(value: Any, default_speed_mps: float) -> tuple[float, bool]:
    values = value if isinstance(value, (tuple, list)) else [value]
    for item in values:
        if isinstance(item, bool):
            continue
        text = str(item).strip().casefold()
        match = re.search(r"\d+(?:\.\d+)?", text)
        if not match:
            continue
        number = _finite_number(match.group(0))
        if number is None or number <= 0:
            continue
        if "mph" in text:
            speed = number * 0.44704
        elif "m/s" in text or "mps" in text:
            speed = number
        else:
            speed = number / 3.6
        if math.isfinite(speed) and speed > 0:
            return speed, False
    return default_speed_mps, True


def _parse_lanes(attrs: Mapping[str, Any], has_reverse: bool, default_lanes: int) -> tuple[int, bool]:
    oneway_value = str(attrs.get("oneway", "")).strip().casefold()
    oneway = oneway_value in {"yes", "true", "1", "-1"}
    if not has_reverse or oneway:
        directional_name = "lanes:backward" if oneway_value == "-1" else "lanes:forward"
        number = _finite_number(attrs.get(directional_name))
        if number is not None and number >= 1 and float(number).is_integer():
            return int(number), False
        number = _finite_number(attrs.get("lanes"))
        if number is not None and number >= 1 and float(number).is_integer():
            return int(number), False
    # A generic lanes tag on a two-way way is total carriageway width, not a
    # verified directional allocation; default per direction and disclose it.
    return default_lanes, True


def _source_provenance(data: OSMData) -> dict[str, Any]:
    metadata = data.metadata
    source_area = metadata.get("source_area", {})
    cache = metadata.get("cache", {})
    return {
        "source": str(metadata.get("source", "unknown")),
        "source_version": str(metadata.get("source_version", "unknown")),
        "retrieved_at": metadata.get("retrieved_at"),
        "city_id": data.area.city_id,
        "area_id": data.area.area_id,
        "boundary_source": data.area.boundary_source,
        "source_area": {
            "source_area_id": source_area.get("source_area_id") if isinstance(source_area, Mapping) else None,
            "source_geometry_sha256": source_area.get("source_geometry_sha256") if isinstance(source_area, Mapping) else None,
            "area_equivalence_verified": cache.get("area_equivalence_verified") if isinstance(cache, Mapping) else None,
        },
        "working_crs": data.area.working_crs,
        "attribution": "© OpenStreetMap contributors" if metadata.get("source") == "OpenStreetMap" else "Synthetic or caller-provided source; verify its attribution.",
        "license": "ODbL-1.0" if metadata.get("source") == "OpenStreetMap" else None,
    }


def load_cached_driving_snapshot(cache_dir: str | Path | None = None) -> OSMData:
    """Load the newest existing local drive graph and never contact OSM."""
    cache = Path(cache_dir) if cache_dir is not None else Path(__file__).resolve().parent / ".cache" / "osm"
    area = normalize_area(DEFAULT_AREA)
    candidates = []
    for graph_path in cache.glob("*-drive.graphml"):
        sidecar_path = graph_path.with_suffix(".json")
        if not sidecar_path.is_file():
            continue
        try:
            metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
            graph = ox.load_graphml(filepath=graph_path)
        except Exception:
            continue
        if metadata.get("mode") == "drive" and graph.is_directed() and graph.number_of_nodes() > 1 and graph.number_of_edges() > 0:
            candidates.append((str(metadata.get("retrieved_at") or ""), graph_path, metadata, graph))
    if not candidates:
        raise FileNotFoundError(f"No usable cached Iași driving graph exists in {cache}; no OSM request was made.")
    _, graph_path, graph_metadata, graph = max(candidates, key=lambda item: (item[0], item[1].name))
    current_key = _area_key(area)
    cached_geometry_hash = graph_metadata.get("source_area_geometry_sha256")
    geometry_match = _source_area_geometry_hash(area) == cached_geometry_hash if cached_geometry_hash else None
    area_match = graph_metadata.get("area_key") == current_key or geometry_match is True
    layers = {name: gpd.GeoDataFrame(geometry=[], crs="EPSG:4326") for name in LAYER_TAGS}
    availability = {name: {"status": "unknown", "feature_count": 0} for name in LAYER_TAGS}
    availability["drive_network"] = {
        "status": "available",
        "node_count": int(graph.number_of_nodes()),
        "edge_count": int(graph.number_of_edges()),
        "coverage": "Existing local OpenStreetMap driving graph; source query area may be unverified.",
    }
    return OSMData(
        area=area,
        graphs={"drive": graph},
        layers=layers,
        layer_availability=availability,
        metadata={
            "source": "OpenStreetMap",
            "source_version": "existing local OSM driving snapshot",
            "retrieved_at": graph_metadata.get("retrieved_at"),
            "cache": {"directory": str(cache), "read_only_reuse": True, "area_equivalence_verified": bool(area_match)},
            "source_area": {
                "source_area_id": graph_metadata.get("area_id"),
                "source_city_id": graph_metadata.get("city_id"),
                "source_boundary_source": graph_metadata.get("boundary_source"),
                "source_geometry_sha256": cached_geometry_hash,
                "equivalence_verified": bool(area_match),
            },
            "graph_cache_key": graph_metadata.get("area_key"),
            "current_area_key": current_key,
            "limitations": [
                "The cached OSM graph is partial and may be outdated.",
                "Legacy sidecars without source geometry cannot verify area equivalence when the cache key differs.",
                "Any demand created by this module is deterministic synthetic demand, not an observed traffic count.",
            ],
        },
        warnings=[] if area_match else ["Cached driving graph area equivalence is unverified; use it only as a local technical demonstration."],
    )


def _write_new_xml(path: Path, root: ET.Element) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing SUMO input or output: {path}")
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _line_parts(
    attrs: Mapping[str, Any],
    u_attrs: Mapping[str, Any],
    v_attrs: Mapping[str, Any],
    source_crs: CRS,
    metric_crs: CRS,
    to_metric: Transformer,
    to_wgs84: Transformer,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]], str]:
    def reproject(coordinates: np.ndarray, transformer: Transformer) -> np.ndarray:
        x, y = transformer.transform(coordinates[:, 0], coordinates[:, 1])
        return np.column_stack((x, y))

    u_metric = (float(u_attrs["x"]), float(u_attrs["y"]))
    v_metric = (float(v_attrs["x"]), float(v_attrs["y"]))
    geometry = attrs.get("geometry")
    if isinstance(geometry, LineString) and not geometry.is_empty and len(geometry.coords) >= 2:
        metric_geometry = transform_geometry(geometry, lambda coordinates: reproject(coordinates, to_metric)) if not source_crs.equals(metric_crs) else geometry
        metric_coords = [(float(x), float(y)) for x, y in metric_geometry.coords]
        wgs_geometry = transform_geometry(geometry, lambda coordinates: reproject(coordinates, to_wgs84)) if not source_crs.equals(CRS.from_epsg(4326)) else geometry
        wgs_coords = [(float(x), float(y)) for x, y in wgs_geometry.coords]
        if math.dist(metric_coords[0], v_metric) < math.dist(metric_coords[0], u_metric):
            metric_coords.reverse()
            wgs_coords.reverse()
        metric_coords[0] = u_metric
        metric_coords[-1] = v_metric
        if all(math.isfinite(value) for point in metric_coords for value in point) and all(math.isfinite(value) for point in wgs_coords for value in point):
            return metric_coords, wgs_coords, "osm_edge_geometry"
    u_wgs = to_wgs84.transform(*((float(u_attrs["x"]), float(u_attrs["y"])))) if not source_crs.equals(CRS.from_epsg(4326)) else (float(u_attrs["x"]), float(u_attrs["y"]))
    v_wgs = to_wgs84.transform(*((float(v_attrs["x"]), float(v_attrs["y"])))) if not source_crs.equals(CRS.from_epsg(4326)) else (float(v_attrs["x"]), float(v_attrs["y"]))
    return [u_metric, v_metric], [(float(u_wgs[0]), float(u_wgs[1])), (float(v_wgs[0]), float(v_wgs[1]))], "node_coordinate_straight_line_fallback"


def _edge_records(data: OSMData, graph: nx.Graph, default_lanes: int, default_speed_mps: float) -> tuple[list[dict[str, Any]], nx.DiGraph, dict[str, Any]]:
    if not graph.is_directed():
        raise SumoPreparationError("The drive graph must preserve directed road connectivity.")
    source_crs_value = graph.graph.get("crs")
    if source_crs_value is None:
        raise SumoPreparationError("The drive graph must declare its CRS.")
    source_crs = CRS.from_user_input(source_crs_value)
    metric_crs = CRS.from_user_input(data.area.working_crs)
    projected = project_graph(graph, metric_crs)
    to_metric = Transformer.from_crs(source_crs, metric_crs, always_xy=True)
    to_wgs84 = Transformer.from_crs(source_crs, CRS.from_epsg(4326), always_xy=True)

    node_ids = {}
    nodes_root = ET.Element("nodes")
    for node, attrs in sorted(projected.nodes(data=True), key=lambda item: _stable_sort(item[0])):
        if "x" not in attrs or "y" not in attrs:
            raise SumoPreparationError(f"Drive node {node!r} has no usable coordinates.")
        x, y = _finite_number(attrs["x"]), _finite_number(attrs["y"])
        if x is None or y is None:
            raise SumoPreparationError(f"Drive node {node!r} has non-finite coordinates.")
        node_id = _stable_id("n_", node)
        node_ids[node] = node_id
        ET.SubElement(nodes_root, "node", {"id": node_id, "x": f"{x:.3f}", "y": f"{y:.3f}", "type": "priority"})

    edge_iterator = graph.edges(keys=True, data=True) if graph.is_multigraph() else ((u, v, 0, attrs) for u, v, attrs in graph.edges(data=True))
    raw_edges = sorted(list(edge_iterator), key=lambda item: (_stable_sort(item[0]), _stable_sort(item[1]), _stable_sort(item[2])))
    reverse_pairs = {(v, u) for u, v, _, _ in raw_edges}
    edge_records = []
    edges_root = ET.Element("edges")
    route_graph = nx.DiGraph()
    route_graph.add_nodes_from(projected.nodes)
    stats = {"defaulted_speed_edge_count": 0, "defaulted_or_ambiguous_lane_edge_count": 0, "straight_line_geometry_fallback_count": 0, "derived_edge_length_count": 0}
    edge_pair_ids: dict[tuple[Any, Any], list[tuple[float, str]]] = {}
    for u, v, key, attrs in raw_edges:
        edge_id = _stable_id("e_", u, v, key)
        metric_shape, wgs_shape, geometry_source = _line_parts(
            attrs,
            projected.nodes[u],
            projected.nodes[v],
            source_crs,
            metric_crs,
            to_metric,
            to_wgs84,
        )
        if projected.is_multigraph():
            metric_attrs = projected.get_edge_data(u, v, key) or {}
        else:
            metric_attrs = projected.get_edge_data(u, v) or {}
        length_m = _finite_number(metric_attrs.get("length_m"))
        if length_m is None or length_m <= 0:
            length_m = sum(math.dist(metric_shape[index - 1], metric_shape[index]) for index in range(1, len(metric_shape)))
            stats["derived_edge_length_count"] += 1
        if not math.isfinite(length_m) or length_m <= 0:
            continue
        speed_mps, speed_defaulted = _parse_speed(attrs.get("maxspeed"), default_speed_mps)
        lanes, lanes_defaulted = _parse_lanes(attrs, (v, u) in reverse_pairs, default_lanes)
        stats["defaulted_speed_edge_count"] += int(speed_defaulted)
        stats["defaulted_or_ambiguous_lane_edge_count"] += int(lanes_defaulted)
        stats["straight_line_geometry_fallback_count"] += int(geometry_source != "osm_edge_geometry")
        edge_element = ET.SubElement(edges_root, "edge", {
            "id": edge_id,
            "from": node_ids[u],
            "to": node_ids[v],
            "priority": "1",
            "numLanes": str(lanes),
            "speed": f"{speed_mps:.3f}",
            "length": f"{length_m:.3f}",
            "shape": " ".join(f"{x:.3f},{y:.3f}" for x, y in metric_shape),
        })
        del edge_element
        osm_way_ids = attrs.get("osmid", attrs.get("osm_id"))
        if osm_way_ids is None:
            osm_way_ids = []
        elif not isinstance(osm_way_ids, (list, tuple, set)):
            osm_way_ids = [osm_way_ids]
        osm_way_ids = sorted(str(value) for value in osm_way_ids)
        record = {
            "sumo_edge_id": edge_id,
            "from_node": u,
            "to_node": v,
            "source_osm_way_ids": osm_way_ids,
            "source_osm_node_ids": [str(u), str(v)],
            "length_m": float(length_m),
            "speed_mps": float(speed_mps),
            "lanes": lanes,
            "geometry_source": geometry_source,
            "geometry_wgs84": wgs_shape,
        }
        edge_records.append(record)
        edge_pair_ids.setdefault((u, v), []).append((float(length_m), edge_id))
        existing = route_graph.get_edge_data(u, v)
        if existing is None or length_m < existing["length_m"] or (length_m == existing["length_m"] and edge_id < existing["sumo_edge_id"]):
            route_graph.add_edge(u, v, length_m=float(length_m), sumo_edge_id=edge_id)

    for values in edge_pair_ids.values():
        values.sort(key=lambda item: (item[0], item[1]))
    return edge_records, route_graph, {
        "nodes_root": nodes_root,
        "edges_root": edges_root,
        "node_ids": node_ids,
        "edge_pair_ids": edge_pair_ids,
        "stats": stats,
        "projected_crs": metric_crs.to_string(),
    }


def _select_demand(
    route_graph: nx.DiGraph,
    edge_pair_ids: Mapping[tuple[Any, Any], list[tuple[float, str]]],
    *,
    vehicle_count: int,
    duration_seconds: float,
    seed: int,
) -> tuple[list[dict[str, Any]], int]:
    rng = random.Random(seed)
    nodes = sorted(route_graph.nodes, key=_stable_sort)
    if len(nodes) < 2:
        return [], 0
    max_attempts = max(100, vehicle_count * 100)
    attempts = 0
    accepted = []
    while len(accepted) < vehicle_count and attempts < max_attempts:
        attempts += 1
        origin = rng.choice(nodes)
        destination = rng.choice(nodes)
        if origin == destination:
            continue
        try:
            node_path = nx.shortest_path(route_graph, origin, destination, weight="length_m")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
        sumo_edges = []
        for left, right in zip(node_path, node_path[1:]):
            options = edge_pair_ids.get((left, right), [])
            if not options:
                sumo_edges = []
                break
            sumo_edges.append(options[0][1])
        if not sumo_edges:
            continue
        accepted.append({
            "vehicle_id": f"arteria_{len(accepted):04d}",
            "origin_osm_node_id": str(origin),
            "destination_osm_node_id": str(destination),
            "sumo_edges": sumo_edges,
            "depart_seconds": round(len(accepted) * duration_seconds * 0.7 / max(vehicle_count, 1), 2),
            "route_length_m_from_osm_graph": round(sum(route_graph[left][right]["length_m"] for left, right in zip(node_path, node_path[1:])), 3),
        })
    return accepted, attempts


def _network_geojson(edge_records: list[dict[str, Any]], provenance: Mapping[str, Any]) -> dict[str, Any]:
    features = []
    for edge in edge_records:
        features.append({
            "type": "Feature",
            "id": edge["sumo_edge_id"],
            "geometry": {"type": "LineString", "coordinates": edge["geometry_wgs84"]},
            "properties": {
                "layer": "converted_driving_edge",
                "sumo_edge_id": edge["sumo_edge_id"],
                "source_osm_way_ids": edge["source_osm_way_ids"],
                "source_osm_node_ids": edge["source_osm_node_ids"],
                "length_m": edge["length_m"],
                "speed_mps": edge["speed_mps"],
                "lanes_per_direction": edge["lanes"],
                "geometry_source": edge["geometry_source"],
            },
        })
    return {"type": "FeatureCollection", "metadata": {"crs": "EPSG:4326", "source": provenance["source"], "retrieved_at": provenance["retrieved_at"], "attribution": provenance["attribution"], "license": provenance["license"]}, "features": features}


def prepare_sumo_network(
    data: OSMData,
    output_dir: str | Path,
    *,
    vehicle_count: int = 20,
    seed: int = 4092,
    duration_seconds: float = 180.0,
    default_lanes: int = DEFAULT_LANES_PER_DIRECTION,
    default_speed_mps: float = DEFAULT_SPEED_MPS,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_edges: int = DEFAULT_MAX_EDGES,
    installation: SumoInstallation | None = None,
) -> dict[str, Any]:
    """Write bounded SUMO plain-XML inputs and deterministic synthetic routes."""
    if isinstance(vehicle_count, bool) or not isinstance(vehicle_count, int) or not 0 <= vehicle_count <= MAX_VEHICLES:
        raise ValueError(f"vehicle_count must be between 0 and {MAX_VEHICLES}.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer.")
    duration = _finite_number(duration_seconds)
    speed_default = _finite_number(default_speed_mps)
    if duration is None or not 1 <= duration <= MAX_DURATION_SECONDS:
        raise ValueError(f"duration_seconds must be between 1 and {MAX_DURATION_SECONDS}.")
    if speed_default is None or speed_default <= 0 or speed_default > 55.0:
        raise ValueError("default_speed_mps must be finite, greater than zero, and no higher than 55 m/s.")
    if isinstance(default_lanes, bool) or not isinstance(default_lanes, int) or not 1 <= default_lanes <= 12:
        raise ValueError("default_lanes must be an integer between 1 and 12.")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in (max_nodes, max_edges)):
        raise ValueError("max_nodes and max_edges must be positive integers.")
    if max_nodes > DEFAULT_MAX_NODES or max_edges > DEFAULT_MAX_EDGES:
        raise ValueError(f"max_nodes/max_edges may lower but cannot exceed hard limits {DEFAULT_MAX_NODES}/{DEFAULT_MAX_EDGES}.")

    graph = data.graphs.get("drive")
    if not isinstance(graph, nx.Graph) or graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        raise SumoPreparationError("A non-empty OSM driving graph is required; walking graphs are not converted into road traffic.")
    if graph.number_of_nodes() > max_nodes or graph.number_of_edges() > max_edges:
        raise SumoPreparationError(
            f"Driving graph exceeds configured bounds ({graph.number_of_nodes()} nodes/{graph.number_of_edges()} edges; "
            f"limits {max_nodes}/{max_edges})."
        )

    edge_records, route_graph, details = _edge_records(data, graph, default_lanes, speed_default)
    if not edge_records:
        raise SumoPreparationError("No directed driving edges with valid positive lengths and coordinates could be converted.")
    demand, attempts = _select_demand(
        route_graph,
        details["edge_pair_ids"],
        vehicle_count=vehicle_count,
        duration_seconds=duration,
        seed=seed,
    )

    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    nodes_path = folder / "iasi.nodes.nod.xml"
    edges_path = folder / "iasi.edges.edg.xml"
    routes_path = folder / "iasi.synthetic.rou.xml"
    network_path = folder / "iasi.net.xml"
    geojson_path = folder / "iasi.network.geojson"
    mapping_path = folder / "iasi.network-id-map.json"
    input_paths = (nodes_path, edges_path, routes_path, geojson_path, mapping_path)
    existing = [path.name for path in input_paths if path.exists()]
    if existing:
        raise FileExistsError("Refusing to overwrite existing SUMO preparation files: " + ", ".join(existing))
    _write_new_xml(nodes_path, details["nodes_root"])
    _write_new_xml(edges_path, details["edges_root"])
    routes_root = ET.Element("routes")
    ET.SubElement(routes_root, "vType", {
        "id": "arteria_passenger",
        "vClass": "passenger",
        "accel": "2.6",
        "decel": "4.5",
        "sigma": "0",
        "length": "5.0",
        "maxSpeed": f"{speed_default:.3f}",
    })
    for item in demand:
        route_id = "route_" + item["vehicle_id"]
        ET.SubElement(routes_root, "route", {"id": route_id, "edges": " ".join(item["sumo_edges"])})
        ET.SubElement(routes_root, "vehicle", {
            "id": item["vehicle_id"],
            "type": "arteria_passenger",
            "route": route_id,
            "depart": f"{item['depart_seconds']:.2f}",
        })
    _write_new_xml(routes_path, routes_root)
    provenance = _source_provenance(data)
    network_geojson = _network_geojson(edge_records, provenance)
    geojson_path.write_text(json.dumps(network_geojson, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    mapping_payload = {
        "schema_version": "arteria.sumo-id-map.v1",
        "source": provenance,
        "nodes": [
            {"sumo_node_id": details["node_ids"][node], "source_graph_node_id": str(node)}
            for node in sorted(details["node_ids"], key=_stable_sort)
        ],
        "edges": [
            {
                "sumo_edge_id": edge["sumo_edge_id"],
                "source_osm_way_ids": edge["source_osm_way_ids"],
                "source_osm_node_ids": edge["source_osm_node_ids"],
            }
            for edge in edge_records
        ],
    }
    mapping_path.write_text(json.dumps(mapping_payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")

    found = installation if installation is not None else discover_sumo()
    conversion_status = "unavailable"
    conversion_detail = "netconvert executable was not found; plain-XML network inputs were prepared but no SUMO network file was built."
    if found.netconvert is not None:
        if network_path.exists():
            raise FileExistsError(f"Refusing to overwrite existing SUMO network: {network_path}")
        try:
            completed = subprocess.run(
                [
                    str(found.netconvert),
                    "--node-files", str(nodes_path),
                    "--edge-files", str(edges_path),
                    "--output-file", str(network_path),
                    "--plain.extend-edge-shape", "true",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            conversion_status = "timeout"
            conversion_detail = "netconvert exceeded the 60-second conversion limit."
        except OSError as error:
            conversion_status = "failed"
            conversion_detail = f"netconvert could not start: {type(error).__name__}: {error}"
        else:
            if completed.returncode == 0 and network_path.is_file() and network_path.stat().st_size > 0:
                conversion_status = "converted"
                conversion_detail = "netconvert produced a SUMO network from the directed metric node/edge inputs."
            else:
                conversion_status = "failed"
                conversion_detail = (completed.stderr or completed.stdout or f"netconvert exited {completed.returncode}")[-2_000:]

    return {
        "schema_version": "arteria.sumo-network-preparation.v1",
        "status": "prepared" if conversion_status in {"unavailable", "converted"} else conversion_status,
        "conversion_status": conversion_status,
        "conversion_detail": conversion_detail,
        "files": {"nodes": nodes_path.name, "edges": edges_path.name, "routes": routes_path.name, "network": network_path.name if conversion_status == "converted" else None, "network_geojson": geojson_path.name, "id_map": mapping_path.name},
        "network": {
            "source_node_count": int(graph.number_of_nodes()),
            "converted_directed_edge_count": len(edge_records),
            "working_crs": details["projected_crs"],
            "default_speed_mps": speed_default,
            "default_lanes_per_direction": default_lanes,
            **details["stats"],
        },
        "demand": {
            "synthetic": True,
            "seed": seed,
            "requested_vehicle_count": vehicle_count,
            "routed_vehicle_count": len(demand),
            "route_search_attempts": attempts,
            "duration_seconds": duration,
            "departure_pattern": "deterministic even spacing within the first 70% of the requested duration to leave an arrival window",
            "routes": demand,
        },
        "source": provenance,
        "limitations": [
            "Vehicle demand is deterministic synthetic demand and is not an observed traffic count.",
            "OSM road connectivity is directed, but turn restrictions, signal plans, lane connectors, and calibration are not verified by this conversion.",
            "Missing speeds use the explicit fallback; missing or ambiguous directional lane counts use the explicit per-direction fallback.",
            "Traffic results from this network would be uncalibrated simulation outputs, not measurements of Iași traffic.",
            *data.warnings,
        ],
    }


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing SUMO output: {path}")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def _trip_features(tripinfo_path: Path, demand: list[dict[str, Any]], edge_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not tripinfo_path.is_file():
        raise SumoPreparationError("SUMO exited without producing tripinfo output; vehicle movement cannot be verified.")
    root = ET.parse(tripinfo_path).getroot()
    trip_rows = {item.get("id"): item for item in root.findall("tripinfo")}
    demand_by_id = {item["vehicle_id"]: item for item in demand}
    edge_by_id = {item["sumo_edge_id"]: item for item in edge_records}
    features = []
    completed = []
    unfinished_records = 0
    not_departed_records = 0
    movement_verified = 0
    for vehicle_id in sorted(trip_rows):
        trip = trip_rows[vehicle_id]
        depart = _finite_number(trip.get("depart"))
        arrival = _finite_number(trip.get("arrival"))
        duration = _finite_number(trip.get("duration"))
        route_length = _finite_number(trip.get("routeLength"))
        waiting = _finite_number(trip.get("waitingTime"))
        if duration is None or route_length is None or waiting is None:
            continue
        if duration > 0 and route_length > 0:
            movement_verified += 1
        is_complete = depart is not None and depart >= 0 and arrival is not None and arrival >= 0 and trip.get("vaporized", "false").casefold() != "true"
        if not is_complete:
            unfinished_records += 1
            if depart is None or depart < 0:
                not_departed_records += 1
            continue
        if duration <= 0 or route_length <= 0:
            continue
        completed.append({"vehicle_id": vehicle_id, "arrival_s": arrival, "duration_s": duration, "route_length_m": route_length, "waiting_time_s": waiting})
        demand_row = demand_by_id.get(vehicle_id, {})
        coordinates = []
        for edge_id in demand_row.get("sumo_edges", []):
            edge = edge_by_id.get(edge_id)
            if not edge:
                continue
            line = edge["geometry_wgs84"]
            if coordinates and line and coordinates[-1] == line[0]:
                coordinates.extend(line[1:])
            else:
                coordinates.extend(line)
        if len(coordinates) >= 2:
            features.append({
                "type": "Feature",
                "id": vehicle_id,
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {**completed[-1], "synthetic_demand": True, "route_trace": "simulated route geometry from the source OSM graph; no live GPS telemetry"},
            })
    metrics = {
        "completed_trip_count": len(completed),
        "incomplete_trip_count": max(0, len(demand) - len(completed)),
        "unfinished_tripinfo_count": unfinished_records,
        "not_departed_tripinfo_count": not_departed_records,
        "unreported_trip_count": max(0, len(demand) - len(trip_rows)),
        "average_trip_duration_s": math.fsum(row["duration_s"] for row in completed) / len(completed) if completed else None,
        "average_waiting_time_s": math.fsum(row["waiting_time_s"] for row in completed) / len(completed) if completed else None,
        "average_simulated_route_length_m": math.fsum(row["route_length_m"] for row in completed) / len(completed) if completed else None,
        "vehicle_movement_verified_count": movement_verified,
    }
    return features, metrics


def run_real_area_simulation(
    data: OSMData,
    output_dir: str | Path,
    *,
    vehicle_count: int = 20,
    seed: int = 4092,
    duration_seconds: float = 180.0,
    execution_timeout_seconds: float = 60.0,
    installation: SumoInstallation | None = None,
) -> dict[str, Any]:
    """Prepare and run a bounded headless SUMO scenario when local binaries exist."""
    timeout = _finite_number(execution_timeout_seconds)
    if timeout is None or not 1 <= timeout <= MAX_EXECUTION_TIMEOUT_SECONDS:
        raise ValueError(f"execution_timeout_seconds must be between 1 and {MAX_EXECUTION_TIMEOUT_SECONDS}.")
    found = installation if installation is not None else discover_sumo()
    prepared = prepare_sumo_network(
        data,
        output_dir,
        vehicle_count=vehicle_count,
        seed=seed,
        duration_seconds=duration_seconds,
        installation=found,
    )
    folder = Path(output_dir)
    result: dict[str, Any] = {
        "schema_version": "arteria.sumo-run.v1",
        "status": "unavailable",
        "execution_mode": "headless_local_sumo",
        "network_preparation": prepared,
        "source": prepared["source"],
        "demand": {key: value for key, value in prepared["demand"].items() if key != "routes"},
        "simulator": {"name": "Eclipse SUMO", "version": None},
        "measurements": None,
        "warnings": [],
    }
    if prepared["conversion_status"] != "converted":
        result["failure_stage"] = "network_conversion"
        result["reason"] = prepared["conversion_detail"]
        result["warnings"].extend(prepared["limitations"])
        _write_new_json(folder / "iasi.simulation.json", result)
        return result
    if found.sumo is None:
        result["failure_stage"] = "binary_discovery"
        result["reason"] = "SUMO executable was not found on PATH or under SUMO_HOME; real-area execution did not start."
        result["warnings"].extend(prepared["limitations"])
        _write_new_json(folder / "iasi.simulation.json", result)
        return result

    network_path = folder / prepared["files"]["network"]
    routes_path = folder / prepared["files"]["routes"]
    tripinfo_path = folder / "iasi.tripinfo.xml"
    geojson_path = folder / "iasi.simulation.geojson"
    expected_outputs = (tripinfo_path, geojson_path, folder / "iasi.simulation.json")
    existing = [path.name for path in expected_outputs if path.exists()]
    if existing:
        raise FileExistsError("Refusing to overwrite existing SUMO results: " + ", ".join(existing))
    try:
        version_result = subprocess.run([str(found.sumo), "--version"], check=True, capture_output=True, text=True, timeout=10)
        run_result = subprocess.run(
            [
                str(found.sumo),
                "--net-file", str(network_path),
                "--route-files", str(routes_path),
                "--tripinfo-output", str(tripinfo_path),
                "--tripinfo-output.write-unfinished", "true",
                "--tripinfo-output.write-undeparted", "true",
                "--seed", str(seed),
                "--step-length", "1.0",
                "--end", f"{duration_seconds:.2f}",
                "--no-step-log", "true",
                "--duration-log.disable", "true",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        result.update({"status": "timeout", "failure_stage": "simulation_execution", "reason": f"SUMO exceeded the {timeout:g}-second wall-clock timeout."})
    except (OSError, subprocess.CalledProcessError) as error:
        result.update({"status": "failed", "failure_stage": "simulation_startup", "reason": f"SUMO could not start or report its version: {type(error).__name__}: {error}"})
    else:
        result["simulator"]["version"] = version_result.stdout.splitlines()[0] if version_result.stdout.splitlines() else "unknown"
        if run_result.returncode != 0:
            result.update({"status": "failed", "failure_stage": "simulation_execution", "reason": (run_result.stderr or run_result.stdout or f"SUMO exited {run_result.returncode}")[-2_000:]})
        else:
            route_features, measurements = _trip_features(tripinfo_path, prepared["demand"]["routes"], _edge_records(data, data.graphs["drive"], DEFAULT_LANES_PER_DIRECTION, DEFAULT_SPEED_MPS)[0])
            network_collection = json.loads((folder / prepared["files"]["network_geojson"]).read_text(encoding="utf-8"))
            _write_new_json(geojson_path, {**network_collection, "features": route_features, "metadata": {**network_collection["metadata"], "layer": "completed_sumo_vehicle_routes", "demand_type": "synthetic"}})
            result.update({
                "status": "completed",
                "measurements": measurements,
                "outputs": {"tripinfo": tripinfo_path.name, "geojson": geojson_path.name},
                "warnings": prepared["limitations"],
            })
    _write_new_json(folder / "iasi.simulation.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent / ".cache" / "iasi-sumo-demo"))
    parser.add_argument("--vehicles", type=int, default=20)
    parser.add_argument("--seed", type=int, default=4092)
    parser.add_argument("--duration", type=float, default=180.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()
    data = load_cached_driving_snapshot()
    result = run_real_area_simulation(
        data,
        args.output_dir,
        vehicle_count=args.vehicles,
        seed=args.seed,
        duration_seconds=args.duration,
        execution_timeout_seconds=args.timeout,
    )
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in {"network_preparation"}}, ensure_ascii=False, indent=2, allow_nan=False))
    print(f"Full result: {Path(args.output_dir) / 'iasi.simulation.json'}")
    return 0 if result["status"] in {"completed", "unavailable"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
