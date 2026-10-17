"""Run a deterministic SIM candidate and multi-route demonstration offline."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import osmnx as ox
from pyproj import Transformer
from shapely.geometry import LineString

from .analysis import analyze_snapshot
from .candidates import discover_intervention_candidates
from .geo import LAYER_TAGS, OSMData, _area_key, _layer_masks, _load_cached_frame, _source_area_geometry_hash, normalize_area
from .impact import evaluate_candidates


DEFAULT_AREA = {
    "city_id": "iasi-ro",
    "area_id": "iasi-central-local-demo",
    "bbox": [27.5755, 47.1610, 27.5825, 47.1655],
    "crs": "EPSG:4326",
    "boundary_source": "user_selected",
}
DEFAULT_OUTPUT = Path(__file__).resolve().parent / ".cache" / "sim-engine-demo"


def _empty_layers() -> dict[str, gpd.GeoDataFrame]:
    return {name: gpd.GeoDataFrame(geometry=[], crs="EPSG:4326") for name in LAYER_TAGS}


def fixture_snapshot() -> OSMData:
    """Build a tiny deterministic graph fixture for offline environments."""
    area = normalize_area(DEFAULT_AREA)
    to_metric = Transformer.from_crs("EPSG:4326", area.working_crs, always_xy=True)
    coordinates = {
        1: (27.5767, 47.1620),
        2: (27.5775, 47.1620),
        3: (27.5783, 47.1620),
        4: (27.5800, 47.1620),
        5: (27.5810, 47.1620),
        6: (27.5780, 47.1640),
        7: (27.5790, 47.1640),
    }
    graph = nx.MultiDiGraph(crs=area.working_crs, name="synthetic-offline-demo")
    graph.graph.update({"arteria_source": "synthetic offline fixture", "arteria_mode": "walk"})
    for node, (longitude, latitude) in coordinates.items():
        x, y = to_metric.transform(longitude, latitude)
        graph.add_node(node, x=x, y=y)
    for left, right in ((1, 2), (2, 3), (6, 7)):
        first = (graph.nodes[left]["x"], graph.nodes[left]["y"])
        second = (graph.nodes[right]["x"], graph.nodes[right]["y"])
        length = float(LineString([first, second]).length)
        graph.add_edge(left, right, key=0, length=length, length_m=length, geometry=LineString([first, second]))
        graph.add_edge(right, left, key=0, length=length, length_m=length, geometry=LineString([second, first]))
    availability = {name: {"status": "unknown", "feature_count": 0} for name in LAYER_TAGS}
    availability["walk_network"] = {"status": "available", "node_count": graph.number_of_nodes(), "edge_count": graph.number_of_edges()}
    return OSMData(
        area=area,
        graphs={"walk": graph},
        layers=_empty_layers(),
        layer_availability=availability,
        metadata={
            "source": "synthetic offline fixture",
            "source_version": "sim.demo.fixture.v1",
            "retrieved_at": None,
            "working_crs": area.working_crs,
            "limitations": ["This demonstration uses synthetic graph nodes and edges; no real OSM observations are included."],
        },
        warnings=["Synthetic offline demonstration data is not evidence about Iași infrastructure."],
    )


def load_cached_snapshot(cache_dir: str | Path | None = None) -> OSMData:
    """Load a suitable local OSM snapshot without issuing any network request."""
    cache = Path(cache_dir) if cache_dir is not None else Path(__file__).resolve().parent / ".cache" / "osm"
    area = normalize_area(DEFAULT_AREA)
    current_key = _area_key(area)
    candidates: list[tuple[str, Path, dict[str, Any]]] = []
    for graph_path in cache.glob("*-walk.graphml"):
        sidecar = graph_path.with_suffix(".json")
        if not sidecar.is_file():
            continue
        try:
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
            graph = ox.load_graphml(filepath=graph_path)
        except Exception:
            continue
        if metadata.get("mode") == "walk" and graph.number_of_nodes() > 1 and graph.number_of_edges() > 0:
            candidates.append((str(metadata.get("retrieved_at") or ""), graph_path, metadata))
    if not candidates:
        raise FileNotFoundError(f"No usable cached Iași walking graph exists in {cache}; the demo made no OSM request.")
    _, graph_path, graph_metadata = max(candidates, key=lambda item: (item[0], item[1].name))
    graph = ox.load_graphml(filepath=graph_path)
    prefix = graph_path.name.removesuffix("-walk.graphml")
    features_path = cache / f"{prefix}-features.geojson"
    features_metadata_path = features_path.with_suffix(".json")
    features = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    features_metadata: dict[str, Any] = {}
    if features_path.is_file() and features_metadata_path.is_file():
        try:
            features_metadata = json.loads(features_metadata_path.read_text(encoding="utf-8"))
            if features_metadata.get("area_key") == graph_metadata.get("area_key"):
                features = _load_cached_frame(features_path)
        except Exception as error:
            features_metadata = {"warning": f"Could not read cached feature layer: {type(error).__name__}: {error}"}
    layers = _layer_masks(features)
    availability = {}
    for name, frame in layers.items():
        status = "available" if len(frame) else ("no_features_returned" if features_metadata and "warning" not in features_metadata else "unknown")
        availability[name] = {"status": status, "feature_count": int(len(frame)), "coverage": "Cached OpenStreetMap tagged features; empty categories do not prove absence."}
    availability["walk_network"] = {"status": "available", "node_count": int(graph.number_of_nodes()), "edge_count": int(graph.number_of_edges())}
    cache_key_matches = graph_metadata.get("area_key") == current_key
    cached_geometry_hash = graph_metadata.get("source_area_geometry_sha256")
    source_geometry_matches = cached_geometry_hash == _source_area_geometry_hash(area) if cached_geometry_hash else None
    area_equivalence_verified = bool(cache_key_matches or source_geometry_matches is True)
    warnings = []
    limitations = [
        "OSM feature and network coverage are partial and may have changed since retrieval.",
        "Legacy cache sidecars without source geometry cannot verify boundary equivalence when their cache key differs from the current area.",
        "Network-node route results do not describe observed trips or population demand.",
    ]
    if not area_equivalence_verified:
        warnings.append("Cached OSM snapshot key differs from the current demo-area key and no matching source-geometry hash is available, so area equivalence is unverified.")
    if "warning" in features_metadata:
        warnings.append(features_metadata["warning"])
    retrieved_at = max(
        [value for value in (graph_metadata.get("retrieved_at"), features_metadata.get("retrieved_at")) if value],
        default=None,
    )
    data = OSMData(
        area=area,
        graphs={"walk": graph},
        layers=layers,
        layer_availability=availability,
        metadata={
            "source": "OpenStreetMap",
            "source_version": "existing local OSM snapshot",
            "retrieved_at": retrieved_at,
            "working_crs": area.working_crs,
            "extent_wgs84": area.extent,
            "area_key": graph_metadata.get("area_key"),
            "current_area_key": current_key,
            "cache": {"directory": str(cache), "read_only_reuse": True, "area_key_matches": cache_key_matches, "source_area_geometry_matches": source_geometry_matches, "area_equivalence_verified": area_equivalence_verified},
            "source_area": {
                "source_area_id": graph_metadata.get("area_id"),
                "source_city_id": graph_metadata.get("city_id"),
                "source_boundary_source": graph_metadata.get("boundary_source"),
                "source_geometry_sha256": cached_geometry_hash,
                "equivalence_verified": area_equivalence_verified,
            },
            "limitations": limitations,
        },
        warnings=warnings,
    )
    return data


def _result_geojson(result: dict[str, Any], data: OSMData) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for candidate in result.get("ranked_candidates", []):
        candidate_id = candidate["candidate_id"]
        features.append({
            "type": "Feature",
            "id": candidate_id,
            "geometry": candidate["geometry"],
            "properties": {"layer": "hypothetical_candidate", "candidate_id": candidate_id, "rank": candidate.get("rank"), "length_m": candidate["length_m"], "screening_status": candidate["screening"]["status"]},
        })
        for route in candidate["impact"].get("routes", []):
            for phase in ("before", "after"):
                geometry = route[phase].get("geometry")
                if geometry is not None:
                    features.append({
                        "type": "Feature",
                        "id": f"{candidate_id}:{route['origin_node_id']}:{route['destination_node_id']}:{phase}",
                        "geometry": geometry,
                        "properties": {"layer": f"{phase}_route", "candidate_id": candidate_id, "origin_node_id": route["origin_node_id"], "destination_node_id": route["destination_node_id"], "outcome": route["outcome"]},
                    })
        for route in candidate.get("targeted_diagnostic_impact", {}).get("routes", []):
            for phase in ("before", "after"):
                geometry = route[phase].get("geometry")
                if geometry is not None:
                    features.append({
                        "type": "Feature",
                        "id": f"{candidate_id}:targeted:{route['origin_node_id']}:{route['destination_node_id']}:{phase}",
                        "geometry": geometry,
                        "properties": {"layer": f"targeted_{phase}_route", "candidate_id": candidate_id, "origin_node_id": route["origin_node_id"], "destination_node_id": route["destination_node_id"], "outcome": route["outcome"], "sample_role": "candidate_specific_targeted_diagnostic"},
                    })
    for candidate in result.get("rejected_candidates", []):
        features.append({
            "type": "Feature",
            "id": candidate["candidate_id"],
            "geometry": candidate["geometry"],
            "properties": {
                "layer": "screened_out_candidate",
                "candidate_id": candidate["candidate_id"],
                "length_m": candidate["length_m"],
                "screening_status": candidate["screening"]["status"],
                "exclusion_reasons": candidate["screening"].get("exclusion_reasons", []),
                "building_classification": candidate["screening"]["mapped_buildings"]["classification"],
            },
        })
    return {
        "type": "FeatureCollection",
        "metadata": {
            "source": data.metadata.get("source"),
            "retrieved_at": data.metadata.get("retrieved_at"),
            "working_crs": data.area.working_crs,
            "attribution": "© OpenStreetMap contributors" if data.metadata.get("source") == "OpenStreetMap" else "Synthetic fixture; no OSM source data.",
            "attribution_url": "https://www.openstreetmap.org/copyright" if data.metadata.get("source") == "OpenStreetMap" else None,
            "license": "ODbL-1.0" if data.metadata.get("source") == "OpenStreetMap" else None,
        },
        "features": features,
    }


def run_demo(source: str = "auto", *, output_dir: str | Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Run the pipeline on cached OSM data or a deterministic offline fixture."""
    if source not in {"auto", "cache", "fixture"}:
        raise ValueError("source must be one of: auto, cache, fixture.")
    data_source = "cache"
    if source == "fixture":
        data, data_source = fixture_snapshot(), "fixture"
    else:
        try:
            data = load_cached_snapshot()
        except FileNotFoundError:
            if source == "cache":
                raise
            data, data_source = fixture_snapshot(), "fixture"
    started = time.perf_counter()
    analysis = analyze_snapshot(data)
    result = evaluate_candidates(data, analysis=analysis)
    result["analysis"] = analysis
    discovery_summary = result.get("candidate_discovery", {})
    result["demo"] = {
        "source_mode": data_source,
        "network_requests_made": False,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "data_source": data.metadata.get("source"),
        "source_retrieved_at": data.metadata.get("retrieved_at"),
        "study_area": analysis["area"],
        "source_area": data.metadata.get("source_area", {
            "source_area_id": data.metadata.get("area_id"),
            "source_city_id": data.metadata.get("city_id"),
            "source_boundary_source": data.metadata.get("boundary_source"),
            "source_geometry_sha256": data.metadata.get("source_area_geometry_sha256"),
            "equivalence_verified": data.metadata.get("cache", {}).get("area_equivalence_verified", True),
        }),
        "candidate_quality": {
            "raw_opportunities": discovery_summary.get("candidate_count_before_limit", 0),
            "deduplicated_opportunities": discovery_summary.get("candidate_count_deduplicated", 0),
            "screened_pool": discovery_summary.get("candidate_count_screened", 0),
            "pool_limit": discovery_summary.get("candidate_pool_limit"),
            "material_conflicts_rejected": discovery_summary.get("candidate_count_rejected_material_conflict", 0),
            "mapped_barrier_conflicts_rejected": discovery_summary.get("candidate_count_rejected_mapped_barrier_conflict", 0),
            "all_conflicts_rejected": discovery_summary.get("candidate_count_rejected_conflict", 0),
            "conditional_candidates": discovery_summary.get("candidate_count_eligible_conditional", 0),
            "returned_ranked_candidates": len(result.get("ranked_candidates", [])),
            "recommendation_status": result.get("recommendation_status"),
        },
        "shared_sample": result.get("sample"),
        "targeted_diagnostic_sample_role": "candidate-specific; local explanatory evidence only; excluded from shared ranking",
        "limitations": data.metadata.get("limitations", []),
    }
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    results_path = folder / "results.json"
    geojson_path = folder / "results.geojson"
    result["output"] = {"json": str(results_path), "geojson": str(geojson_path)}
    serialized = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    geojson_serialized = json.dumps(_result_geojson(result, data), ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    results_path.write_text(serialized, encoding="utf-8", newline="\n")
    geojson_path.write_text(geojson_serialized, encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("auto", "cache", "fixture"), default="auto", help="use cached OSM data when available or a synthetic fixture; never downloads")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="directory for generated JSON and GeoJSON results")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = run_demo(args.source, output_dir=args.output_dir)
    aggregate_candidates = result.get("ranked_candidates", [])
    print(f"SIM demo source: {result['demo']['source_mode']} ({result['demo']['data_source']})")
    print(f"Network requests: {result['demo']['network_requests_made']}; area: {result['area_id']}")
    quality = result["demo"]["candidate_quality"]
    print(
        "Candidate screening: "
        f"{quality['raw_opportunities']} raw → {quality['screened_pool']} screened "
        f"(limit {quality['pool_limit']}); {quality['material_conflicts_rejected']} material conflicts rejected; "
        f"{quality['conditional_candidates']} conditional candidates"
    )
    print(f"Candidates returned: {len(aggregate_candidates)}; shared sample routes per candidate: {result.get('sample', {}).get('evaluated_pair_count', 0)}")
    for candidate in aggregate_candidates:
        aggregate = candidate["impact"]["aggregate"]
        targeted = candidate.get("targeted_diagnostic_impact", {}).get("aggregate") or {}
        print(
            f"  rank {candidate['rank']}: {candidate['candidate_id']} — "
            f"{aggregate['improved_count']} improved, {aggregate['newly_reachable_count']} newly reachable, "
            f"{aggregate['regressed_count']} regressed in shared sample; "
            f"{targeted.get('newly_reachable_count', 0)} newly reachable in targeted diagnostic; "
            f"length {candidate['length_m']:.1f} m; {candidate['screening']['recommendation_status']}"
        )
    print(f"Recommendation: {result.get('recommendation_status')}")
    print(f"JSON: {result['output']['json']}")
    print(f"GeoJSON: {result['output']['geojson']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
