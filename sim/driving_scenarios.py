"""Bounded paired SUMO driving scenarios with explicit source provenance."""

from __future__ import annotations

import copy
import hashlib
import json
import statistics
import subprocess
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import networkx as nx

from .geo import OSMData, _source_area_geometry_hash
from .sumo_engine import (
    DEFAULT_MAX_EDGES,
    DEFAULT_MAX_NODES,
    DEFAULT_LANES_PER_DIRECTION,
    DEFAULT_SPEED_MPS,
    MAX_DURATION_SECONDS,
    MAX_EXECUTION_TIMEOUT_SECONDS,
    MAX_VEHICLES,
    SumoPreparationError,
    _edge_records,
    _finished_vehicle_ids,
    _finite_number,
    _select_demand,
    _source_provenance,
    _stable_id,
    _trip_features,
    _vehroute_features,
    _write_new_json,
    prepare_sumo_network,
)
from .sumo_support import SumoInstallation, discover_sumo


DRIVING_INTERVENTION_SCHEMA = "arteria.driving-intervention.v1"
DRIVING_INTERVENTION_CATALOG_SCHEMA = "arteria.driving-intervention-catalog.v1"
SUMO_COMPARISON_SCHEMA = "arteria.sumo-comparison.v1"
SUPPORTED_DRIVING_ACTION = "set_drive_edge_speed_limit"


def _network_revision(data: OSMData, edge_records: list[dict[str, Any]]) -> str:
    stable_records = [
        {
            key: record[key]
            for key in (
                "sumo_edge_id", "from_node", "to_node", "source_osm_way_ids", "source_osm_node_ids",
                "length_m", "speed_mps", "lanes", "geometry_source", "geometry_wgs84",
            )
        }
        for record in sorted(edge_records, key=lambda item: item["sumo_edge_id"])
    ]
    payload = {
        "area_geometry_sha256": _source_area_geometry_hash(data.area),
        "edges": stable_records,
        "schema_version": "arteria.sumo-network-revision.v1",
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def get_driving_intervention_catalog(data: OSMData | None = None) -> dict[str, Any]:
    """Describe one currently supported OSM-drive-graph edit; no feasibility is implied."""
    result: dict[str, Any] = {
        "schema_version": DRIVING_INTERVENTION_CATALOG_SCHEMA,
        "status": "operation_schema_only" if data is None else "available",
        "supported_actions": [{
            "action": SUPPORTED_DRIVING_ACTION,
            "target_type": "directed SUMO edge ID bound to one network revision",
            "parameters": {"speed_limit_mps": {"type": "number", "minimum": 1.0, "maximum": 55.0}},
            "meaning": "Changes the modeled speed attribute on one directed OSM graph edge for a paired SUMO comparison.",
            "physical_feasibility": "unknown",
            "legal_status": "unknown",
            "recommendation_status": "not_evaluated",
        }],
        "network_revision": None,
        "targets": [],
        "limitations": [
            "Catalog targets identify graph edges only; they do not establish ownership, legal authority, field conditions, or implementation feasibility.",
            "SUMO outputs are simulated outputs on an incomplete OSM network, not observed traffic measurements.",
        ],
    }
    if data is None:
        return result
    graph = data.graphs.get("drive")
    if not isinstance(graph, nx.Graph) or not graph.number_of_nodes() or not graph.number_of_edges():
        result["status"] = "unavailable"
        result["reason"] = "A non-empty directed drive graph is required to enumerate exact edge targets."
        return result
    if not graph.is_directed():
        result["status"] = "unavailable"
        result["reason"] = "The source road graph is not directed; no executable edge targets were exposed."
        return result
    if graph.number_of_nodes() > DEFAULT_MAX_NODES or graph.number_of_edges() > DEFAULT_MAX_EDGES:
        result["status"] = "unavailable"
        result["reason"] = f"The source graph exceeds the catalog bounds ({DEFAULT_MAX_NODES} nodes/{DEFAULT_MAX_EDGES} edges)."
        result["observed_graph_size"] = {"node_count": graph.number_of_nodes(), "directed_edge_count": graph.number_of_edges()}
        return result
    records, _, _ = _edge_records(data, graph, DEFAULT_LANES_PER_DIRECTION, DEFAULT_SPEED_MPS)
    revision = _network_revision(data, records)
    result["network_revision"] = revision
    result["targets"] = [
        {
            "sumo_edge_id": edge["sumo_edge_id"],
            "network_revision": revision,
            "source_osm_way_ids": edge["source_osm_way_ids"],
            "source_osm_node_ids": edge["source_osm_node_ids"],
            "source_speed_mps": edge["speed_mps"],
            "geometry_source": edge["geometry_source"],
        }
        for edge in records
    ]
    result["source"] = _source_provenance(data)
    return result


def _validate_intervention(data: OSMData, edge_records: list[dict[str, Any]], intervention: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    unsupported_keys = set(intervention) - {"schema_version", "action", "target", "parameters"}
    if unsupported_keys:
        raise ValueError(f"intervention contains unsupported field(s): {sorted(unsupported_keys)!r}.")
    if intervention.get("schema_version") != DRIVING_INTERVENTION_SCHEMA:
        raise ValueError(f"intervention.schema_version must be {DRIVING_INTERVENTION_SCHEMA!r}.")
    if intervention.get("action") != SUPPORTED_DRIVING_ACTION:
        raise ValueError(f"Only {SUPPORTED_DRIVING_ACTION!r} is supported by the paired SUMO evaluator.")
    target = intervention.get("target")
    parameters = intervention.get("parameters")
    if not isinstance(target, Mapping) or not isinstance(parameters, Mapping):
        raise ValueError("intervention.target and intervention.parameters must be mappings.")
    edge_id = target.get("sumo_edge_id")
    if not isinstance(edge_id, str):
        raise ValueError("intervention.target.sumo_edge_id must be a string from the current intervention catalog.")
    if set(target) - {
        "sumo_edge_id", "network_revision", "source_osm_way_ids", "source_osm_node_ids",
        "source_speed_mps", "geometry_source",
    }:
        raise ValueError("intervention.target contains unsupported fields.")
    if set(parameters) != {"speed_limit_mps"}:
        raise ValueError("intervention.parameters must contain only speed_limit_mps.")
    by_id = {edge["sumo_edge_id"]: edge for edge in edge_records}
    edge = by_id.get(edge_id)
    if edge is None:
        raise ValueError("intervention target must identify an exact directed edge in the current drive graph.")
    revision = _network_revision(data, edge_records)
    if target.get("network_revision") != revision:
        raise ValueError("intervention target network_revision is stale or does not match the current drive graph.")
    source_ways = target.get("source_osm_way_ids")
    if not isinstance(source_ways, list) or source_ways != edge["source_osm_way_ids"]:
        raise ValueError("intervention target source_osm_way_ids must match the current source OSM edge identity.")
    source_nodes = target.get("source_osm_node_ids")
    if source_nodes is not None and source_nodes != edge["source_osm_node_ids"]:
        raise ValueError("intervention target source_osm_node_ids must match the current source graph edge identity.")
    source_speed = target.get("source_speed_mps")
    if source_speed is not None and _finite_number(source_speed) != edge["speed_mps"]:
        raise ValueError("intervention target source_speed_mps must match the current source graph edge speed.")
    geometry_source = target.get("geometry_source")
    if geometry_source is not None and geometry_source != edge["geometry_source"]:
        raise ValueError("intervention target geometry_source must match the current source graph edge geometry.")
    raw_speed = parameters.get("speed_limit_mps")
    speed = _finite_number(raw_speed) if isinstance(raw_speed, (int, float)) and not isinstance(raw_speed, bool) else None
    if speed is None or not 1.0 <= speed <= 55.0:
        raise ValueError("parameters.speed_limit_mps must be a finite value from 1 through 55 m/s.")
    normalized = {
        "schema_version": DRIVING_INTERVENTION_SCHEMA,
        "action": SUPPORTED_DRIVING_ACTION,
        "target": {
            "sumo_edge_id": edge_id,
            "network_revision": revision,
            "source_osm_way_ids": list(edge["source_osm_way_ids"]),
            "source_osm_node_ids": list(edge["source_osm_node_ids"]),
        },
        "parameters": {"speed_limit_mps": speed},
        "validation": {
            "status": "validated_for_graph_edit",
            "physical_feasibility": "unknown",
            "legal_status": "unknown",
            "recommendation_status": "not_evaluated",
        },
    }
    return normalized, edge


def _read_completed_trip_metrics(path: Path) -> dict[str, dict[str, float]]:
    if not path.is_file():
        return {}
    root = ET.parse(path).getroot()
    completed: dict[str, dict[str, float]] = {}
    for row in root.findall("tripinfo"):
        vehicle_id = row.get("id")
        values = {key: _finite_number(row.get(source)) for key, source in (
            ("duration_s", "duration"), ("waiting_time_s", "waitingTime"), ("route_length_m", "routeLength"),
            ("depart_s", "depart"), ("arrival_s", "arrival"),
        )}
        if not vehicle_id or any(value is None for value in values.values()):
            continue
        if values["depart_s"] is None or values["depart_s"] < 0 or values["arrival_s"] is None or values["arrival_s"] < 0:
            continue
        if row.get("vaporized", "false").casefold() == "true" or values["duration_s"] <= 0 or values["route_length_m"] <= 0:
            continue
        completed[vehicle_id] = {key: float(value) for key, value in values.items() if key not in {"depart_s", "arrival_s"} and value is not None}
    return completed


def _actual_route_sequences(
    path: Path,
    finished_ids: set[str],
    edge_records: list[dict[str, Any]],
) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    if not path.is_file():
        return {}, []
    root = ET.parse(path).getroot()
    sequences: dict[str, tuple[str, ...]] = {}
    invalid_ids: list[str] = []
    edge_by_id = {edge["sumo_edge_id"]: edge for edge in edge_records}
    for vehicle in root.findall("vehicle"):
        vehicle_id = vehicle.get("id")
        route = vehicle.find("route")
        if vehicle_id in finished_ids and route is not None:
            edges = tuple(route.get("edges", "").split())
            if edges:
                records = [edge_by_id.get(edge_id) for edge_id in edges]
                if any(record is None for record in records) or any(
                    str(left["to_node"]) != str(right["from_node"])
                    for left, right in zip(records, records[1:])
                    if left is not None and right is not None
                ):
                    invalid_ids.append(vehicle_id)
                else:
                    sequences[vehicle_id] = edges
    return sequences, invalid_ids


def _run_side(
    data: OSMData,
    folder: Path,
    *,
    vehicle_count: int,
    seed: int,
    duration_seconds: float,
    timeout: float,
    installation: SumoInstallation,
    demand_plan: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        prepared = prepare_sumo_network(
            data, folder, vehicle_count=vehicle_count, seed=seed, duration_seconds=duration_seconds,
            installation=installation, demand_plan=demand_plan,
        )
    except (SumoPreparationError, ValueError, OSError) as error:
        return {
            "status": "preparation_failed",
            "reason": f"{type(error).__name__}: {error}",
            "requested_vehicle_count": vehicle_count,
            "generated_vehicle_count": len(demand_plan.get("routes", [])),
            "departed_vehicle_count": None,
            "finished_vehicle_count": None,
            "unfinished_vehicle_count": None,
            "not_departed_vehicle_count": None,
            "unreported_vehicle_count": None,
            "measurements": None,
            "outputs": {},
            "warnings": [],
        }
    run: dict[str, Any] = {
        "status": "unavailable",
        "network_preparation": prepared,
        "requested_vehicle_count": vehicle_count,
        "generated_vehicle_count": prepared["demand"]["routed_vehicle_count"],
        "departed_vehicle_count": None,
        "finished_vehicle_count": None,
        "unfinished_vehicle_count": None,
        "not_departed_vehicle_count": None,
        "unreported_vehicle_count": None,
        "simulation_horizon_seconds": duration_seconds,
        "tripinfo_file_present": False,
        "vehroute_file_present": False,
        "measurements": None,
        "outputs": {"network_geojson": prepared["files"]["network_geojson"]},
        "warnings": list(prepared["limitations"]),
    }
    if prepared["conversion_status"] != "converted":
        run["status"] = "preparation_failed" if prepared["conversion_status"] in {"failed", "timeout"} else "unavailable"
        run["reason"] = prepared["conversion_detail"]
        return run
    if installation.sumo is None:
        run["reason"] = "SUMO executable is unavailable; only bounded network preparation was produced."
        return run

    tripinfo = folder / "iasi.tripinfo.xml"
    vehroute = folder / "iasi.vehroute.xml"
    route_geojson = folder / "iasi.simulation.geojson"
    expected = (tripinfo, vehroute, route_geojson, folder / "iasi.simulation.json")
    existing = [path.name for path in expected if path.exists()]
    if existing:
        raise FileExistsError("Refusing to overwrite existing paired SUMO outputs: " + ", ".join(existing))
    try:
        version = subprocess.run([str(installation.sumo), "--version"], check=True, capture_output=True, text=True, timeout=10)
        executed = subprocess.run([
            str(installation.sumo), "--net-file", str(folder / prepared["files"]["network"]),
            "--route-files", str(folder / prepared["files"]["routes"]),
            "--tripinfo-output", str(tripinfo), "--tripinfo-output.write-unfinished", "true",
            "--tripinfo-output.write-undeparted", "true", "--vehroute-output", str(vehroute),
            "--vehroute-output.write-unfinished", "true", "--vehroute-output.exit-times", "true",
            "--vehroute-output.route-length", "true", "--seed", str(seed), "--step-length", "1.0",
            "--end", f"{duration_seconds:.2f}", "--no-step-log", "true", "--duration-log.disable", "true",
        ], check=False, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        run.update({"status": "timeout", "reason": f"SUMO exceeded the {timeout:g}-second wall-clock timeout."})
        return run
    except (OSError, subprocess.CalledProcessError) as error:
        run.update({"status": "failed", "reason": f"SUMO startup failed: {type(error).__name__}: {error}"})
        return run
    run["simulator_version"] = version.stdout.splitlines()[0] if version.stdout.splitlines() else "unknown"
    if executed.returncode != 0:
        run.update({"status": "failed", "reason": (executed.stderr or executed.stdout or f"SUMO exited {executed.returncode}")[-2_000:]})
        return run
    run["tripinfo_file_present"] = tripinfo.is_file()
    run["vehroute_file_present"] = vehroute.is_file()
    try:
        edge_records, _, _ = _edge_records(data, data.graphs["drive"], DEFAULT_LANES_PER_DIRECTION, DEFAULT_SPEED_MPS)
        _, measurements = _trip_features(tripinfo, prepared["demand"]["routes"], edge_records)
        finished = _finished_vehicle_ids(tripinfo)
        route_features, warnings = _vehroute_features(vehroute, prepared["demand"]["routes"], edge_records, finished)
        network_collection = json.loads((folder / prepared["files"]["network_geojson"]).read_text(encoding="utf-8"))
        _write_new_json(route_geojson, {
            **network_collection,
            "features": route_features,
            "metadata": {
                **network_collection["metadata"], "layer": "completed_sumo_vehicle_routes", "demand_type": "synthetic",
                "route_geometry_source": "SUMO vehroute-output edge sequence mapped to source OSM edge geometry",
                "route_geometry_is_timestep_gps": False,
            },
        })
    except (SumoPreparationError, OSError, ET.ParseError, json.JSONDecodeError, ValueError) as error:
        run.update({"status": "failed", "reason": f"SUMO output could not be verified: {type(error).__name__}: {error}"})
        return run
    reported_departed = max(0, measurements["completed_trip_count"] + measurements["unfinished_tripinfo_count"] - measurements["not_departed_tripinfo_count"])
    run.update({
        "status": "completed",
        "simulator_version": run["simulator_version"],
        "tripinfo_file_present": tripinfo.is_file(),
        "vehroute_file_present": vehroute.is_file(),
        "departed_vehicle_count": reported_departed,
        "finished_vehicle_count": measurements["completed_trip_count"],
        "unfinished_vehicle_count": max(0, reported_departed - measurements["completed_trip_count"]),
        "not_departed_vehicle_count": measurements["not_departed_tripinfo_count"],
        "unreported_vehicle_count": measurements["unreported_trip_count"],
        "measurements": measurements,
        "outputs": {"network_geojson": prepared["files"]["network_geojson"], "tripinfo": tripinfo.name, "vehroute": vehroute.name if vehroute.is_file() else None, "geojson": route_geojson.name},
        "warnings": [*run["warnings"], *warnings],
    })
    return run


def _paired_comparison(baseline: Path, scenario: Path, edge_records: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_finished = _finished_vehicle_ids(baseline / "iasi.tripinfo.xml")
    scenario_finished = _finished_vehicle_ids(scenario / "iasi.tripinfo.xml")
    baseline_metrics = _read_completed_trip_metrics(baseline / "iasi.tripinfo.xml")
    scenario_metrics = _read_completed_trip_metrics(scenario / "iasi.tripinfo.xml")
    baseline_routes, baseline_invalid = _actual_route_sequences(baseline / "iasi.vehroute.xml", baseline_finished, edge_records)
    scenario_routes, scenario_invalid = _actual_route_sequences(scenario / "iasi.vehroute.xml", scenario_finished, edge_records)
    shared_ids = sorted(set(baseline_metrics) & set(scenario_metrics))
    same_route_ids = [vehicle_id for vehicle_id in shared_ids if baseline_routes.get(vehicle_id) and baseline_routes.get(vehicle_id) == scenario_routes.get(vehicle_id)]
    excluded = [vehicle_id for vehicle_id in shared_ids if vehicle_id not in same_route_ids]
    metrics: dict[str, Any] | None = None
    if same_route_ids:
        metrics = {}
        for key in ("duration_s", "waiting_time_s", "route_length_m"):
            before = [baseline_metrics[item][key] for item in same_route_ids]
            after = [scenario_metrics[item][key] for item in same_route_ids]
            metrics[key] = {
                "baseline_mean": statistics.fmean(before),
                "scenario_mean": statistics.fmean(after),
                "scenario_minus_baseline_mean": statistics.fmean(after) - statistics.fmean(before),
                "paired_vehicle_count": len(same_route_ids),
            }
    return {
        "status": "comparable_pairs_available" if same_route_ids else "no_comparable_completed_pairs",
        "pairing_rule": "Same synthetic vehicle ID, completed in both runs, with the same SUMO-reported edge sequence in both runs.",
        "paired_vehicle_count": len(same_route_ids),
        "shared_completed_vehicle_count": len(shared_ids),
        "excluded_route_changed_or_unreported_count": len(excluded),
        "excluded_vehicle_ids": excluded,
        "invalid_or_disconnected_route_vehicle_ids": sorted(set(baseline_invalid) | set(scenario_invalid)),
        "metrics": metrics,
        "interpretation": "Paired differences are uncalibrated SUMO outputs from synthetic demand; they are not measured traffic impacts or forecasts.",
    }


def evaluate_driving_scenario(
    data: OSMData,
    intervention: Mapping[str, Any],
    output_dir: str | Path,
    *,
    vehicle_count: int = 20,
    seed: int = 4092,
    duration_seconds: float = 180.0,
    execution_timeout_seconds: float = 60.0,
    installation: SumoInstallation | None = None,
) -> dict[str, Any]:
    """Run bounded baseline and one isolated driving-edge edit on identical demand."""
    if isinstance(vehicle_count, bool) or not isinstance(vehicle_count, int) or not 1 <= vehicle_count <= MAX_VEHICLES:
        raise ValueError(f"vehicle_count must be an integer from 1 through {MAX_VEHICLES}.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer.")
    duration = _finite_number(duration_seconds)
    timeout = _finite_number(execution_timeout_seconds)
    if duration is None or not 1 <= duration <= MAX_DURATION_SECONDS:
        raise ValueError(f"duration_seconds must be between 1 and {MAX_DURATION_SECONDS}.")
    if timeout is None or not 1 <= timeout <= MAX_EXECUTION_TIMEOUT_SECONDS:
        raise ValueError(f"execution_timeout_seconds must be between 1 and {MAX_EXECUTION_TIMEOUT_SECONDS}.")
    graph = data.graphs.get("drive")
    if not isinstance(graph, nx.Graph) or not graph.is_directed() or not graph.number_of_nodes() or not graph.number_of_edges():
        raise SumoPreparationError("A non-empty directed drive graph is required for paired SUMO evaluation.")
    if graph.number_of_nodes() > DEFAULT_MAX_NODES or graph.number_of_edges() > DEFAULT_MAX_EDGES:
        raise SumoPreparationError(f"Driving graph exceeds paired-run bounds ({DEFAULT_MAX_NODES} nodes/{DEFAULT_MAX_EDGES} directed edges).")
    if not isinstance(intervention, Mapping):
        raise ValueError("intervention must be a mapping returned from the versioned driving catalog.")
    source_data = copy.deepcopy(data)
    graph = source_data.graphs["drive"]
    baseline_edges, route_graph, details = _edge_records(source_data, graph, DEFAULT_LANES_PER_DIRECTION, DEFAULT_SPEED_MPS)
    normalized, selected_edge = _validate_intervention(source_data, baseline_edges, intervention)
    demand, attempts = _select_demand(route_graph, details["edge_pair_ids"], vehicle_count=vehicle_count, duration_seconds=duration, seed=seed)
    demand_plan = {"routes": demand, "route_search_attempts": attempts}
    demand_hash = hashlib.sha256(json.dumps(demand_plan, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()

    folder = Path(output_dir)
    if folder.exists():
        if not folder.is_dir():
            raise FileExistsError(f"Output path is not a directory: {folder}")
        existing = list(folder.iterdir())
        if existing:
            raise FileExistsError("Refusing to use a non-empty paired SUMO output directory: " + ", ".join(item.name for item in existing[:10]))
    else:
        folder.mkdir(parents=True)
    baseline_folder = folder / "baseline"
    scenario_folder = folder / "scenario"

    scenario_graph = copy.deepcopy(graph)
    target_id = selected_edge["sumo_edge_id"]
    matched = 0
    iterator = scenario_graph.edges(keys=True, data=True) if scenario_graph.is_multigraph() else ((u, v, 0, attrs) for u, v, attrs in scenario_graph.edges(data=True))
    for u, v, key, attrs in iterator:
        # IDs include the multigraph key; use the same stable ID helper as conversion.
        if _stable_id("e_", u, v, key) == target_id:
            attrs["maxspeed"] = normalized["parameters"]["speed_limit_mps"] * 3.6
            matched += 1
    if matched != 1:
        raise ValueError("Intervention target did not resolve to exactly one source graph edge.")
    scenario_data = copy.deepcopy(source_data)
    scenario_data.graphs["drive"] = scenario_graph
    found = installation if installation is not None else discover_sumo()
    baseline_result = _run_side(source_data, baseline_folder, vehicle_count=vehicle_count, seed=seed, duration_seconds=duration, timeout=timeout, installation=found, demand_plan=demand_plan)
    scenario_result = _run_side(scenario_data, scenario_folder, vehicle_count=vehicle_count, seed=seed, duration_seconds=duration, timeout=timeout, installation=found, demand_plan=demand_plan)

    statuses = {baseline_result["status"], scenario_result["status"]}
    if "preparation_failed" in statuses:
        status = "preparation_failed"
    elif "timeout" in statuses:
        status = "timeout"
    elif "failed" in statuses:
        status = "failed"
    elif "unavailable" in statuses:
        status = "unavailable"
    else:
        status = "completed"
    comparison = _paired_comparison(baseline_folder, scenario_folder, baseline_edges) if status == "completed" else None
    edge_collection = json.loads((scenario_folder / "iasi.network.geojson").read_text(encoding="utf-8")) if (scenario_folder / "iasi.network.geojson").is_file() else None
    changed_geometry = None
    if edge_collection:
        changed_geometry = {
            "type": "FeatureCollection", "features": [feature for feature in edge_collection.get("features", []) if feature.get("id") == target_id or feature.get("properties", {}).get("sumo_edge_id") == target_id],
            "metadata": {
                **edge_collection.get("metadata", {}),
                "layer": "modeled_speed_limit_target",
                "source_osm_way_ids": selected_edge["source_osm_way_ids"],
                "network_revision": _network_revision(source_data, baseline_edges),
                "physical_feasibility": "unknown",
            },
        }
        _write_new_json(scenario_folder / "iasi.changed-edge.geojson", changed_geometry)
    network_revision = _network_revision(source_data, baseline_edges)
    baseline_run_id = "sumo_run_" + hashlib.sha256(f"{network_revision}|{demand_hash}|baseline|{seed}|{duration}".encode("utf-8")).hexdigest()[:20]
    scenario_run_id = "sumo_run_" + hashlib.sha256(f"{network_revision}|{demand_hash}|{normalized['action']}|{target_id}|{normalized['parameters']['speed_limit_mps']}|{seed}|{duration}".encode("utf-8")).hexdigest()[:20]
    result_warnings = [warning for run in (baseline_result, scenario_result) for warning in run.get("warnings", [])]
    result = {
        "schema_version": SUMO_COMPARISON_SCHEMA,
        "status": status,
        "execution_mode": "bounded_local_sumo_paired_runs",
        "study_area": {"city_id": source_data.area.city_id, "area_id": source_data.area.area_id, "boundary_source": source_data.area.boundary_source, "geometry_wgs84": source_data.area.geojson, "extent_wgs84": source_data.area.extent, "working_crs": source_data.area.working_crs},
        "source": _source_provenance(source_data),
        "source_area_verification": _source_provenance(source_data)["source_area_verification"],
        "network_revision": network_revision,
        "baseline_run_id": baseline_run_id,
        "scenario_run_id": scenario_run_id,
        "intervention": normalized,
        "intervention_validation": normalized["validation"],
        "seed": seed,
        "demand": {
            "synthetic": True, "seed": seed, "requested_vehicle_count": vehicle_count,
            "generated_vehicle_count": len(demand), "route_search_attempts": attempts,
            "sha256": demand_hash,
            "duration_seconds": duration,
        },
        "route_selection_policy": "Deterministic Python Random(seed) selection of directed shortest paths weighted by OSM graph length; one plan is generated once and the exact vehicle IDs, OD endpoints, route edge IDs and departures are reused in both runs.",
        "simulation_configuration": {"seed": seed, "duration_seconds": duration, "execution_timeout_seconds_per_run": timeout, "vehicle_count_limit": MAX_VEHICLES, "duration_limit_seconds": MAX_DURATION_SECONDS, "wall_clock_timeout_limit_seconds": MAX_EXECUTION_TIMEOUT_SECONDS, "step_length_seconds": 1.0, "default_speed_mps": DEFAULT_SPEED_MPS, "default_lanes_per_direction": DEFAULT_LANES_PER_DIRECTION},
        "simulator": {"name": "Eclipse SUMO", "version": baseline_result.get("simulator_version")},
        "configuration": {"baseline": {"default_speed_mps": DEFAULT_SPEED_MPS, "default_lanes_per_direction": DEFAULT_LANES_PER_DIRECTION}, "scenario": {"target_speed_limit_mps": normalized["parameters"]["speed_limit_mps"]}},
        "baseline": baseline_result,
        "scenario": scenario_result,
        "comparison": comparison,
        "warnings": result_warnings,
        "outputs": {
            "baseline_network_geojson": f"baseline/{baseline_result['outputs']['network_geojson']}" if baseline_result["outputs"].get("network_geojson") else None,
            "baseline_simulation_geojson": f"baseline/{baseline_result['outputs'].get('geojson')}" if baseline_result["outputs"].get("geojson") else None,
            "scenario_network_geojson": f"scenario/{scenario_result['outputs']['network_geojson']}" if scenario_result["outputs"].get("network_geojson") else None,
            "scenario_simulation_geojson": f"scenario/{scenario_result['outputs'].get('geojson')}" if scenario_result["outputs"].get("geojson") else None,
            "changed_edge_geojson": "scenario/iasi.changed-edge.geojson" if changed_geometry and changed_geometry["features"] else None,
            "network_geojson_contains_target": bool(changed_geometry and changed_geometry["features"]),
        },
        "limitations": [
            "Demand is deterministic synthetic OSM graph demand, not observed traffic.",
            "SUMO results are uncalibrated simulated outputs; they are not measured traffic or forecasts.",
            "The intervention changes one modeled edge speed attribute only; legal and physical feasibility remain unknown.",
            "SUMO-reported route edge geometry is mapped to source OSM geometry and is not timestep GPS telemetry.",
        ],
    }
    _write_new_json(folder / "iasi.sumo-comparison.json", result)
    return result
