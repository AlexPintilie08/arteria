"""Offline tests for the geospatial pipeline and scenario engine."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import networkx as nx
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, Polygon

from sim.analysis import analyze_snapshot, network_metrics, route_between
from sim import geo as geo_module
from sim.geo import AreaValidationError, LAYER_TAGS, OSMData, acquire_osm_data, feature_collection, normalize_area
from sim.scenario import InterventionError, evaluate_pedestrian_connection, evaluate_scenario


def _fixture_data(*, disconnected: bool = True, with_school: bool = True) -> OSMData:
    boundary = Polygon([
        (27.575, 47.155), (27.590, 47.155), (27.590, 47.170),
        (27.575, 47.170), (27.575, 47.155),
    ])
    area = normalize_area({
        "city_id": "iasi-ro",
        "area_id": "iasi-test-area",
        "boundary": boundary,
        "crs": "EPSG:4326",
        "boundary_source": "test_fixture",
    })
    graph = nx.MultiDiGraph(crs="EPSG:4326", name="offline-fixture")
    graph.add_node(1, x=27.580, y=47.160)
    graph.add_node(2, x=27.581, y=47.160)
    graph.add_node(3, x=27.582, y=47.160)
    if disconnected:
        graph.add_node(4, x=27.585, y=47.160)
    for u, v, length in ((1, 2, 100.0), (2, 3, 100.0)):
        line = LineString([(graph.nodes[u]["x"], graph.nodes[u]["y"]), (graph.nodes[v]["x"], graph.nodes[v]["y"])])
        graph.add_edge(u, v, key=0, length=length, length_m=length, osmid=f"{u}-{v}", geometry=line)
        graph.add_edge(v, u, key=0, length=length, length_m=length, osmid=f"{u}-{v}", geometry=LineString(list(line.coords)[::-1]))
    layers = {name: gpd.GeoDataFrame({"osm_id": [], "geometry": []}, geometry="geometry", crs="EPSG:4326") for name in LAYER_TAGS}
    availability = {name: {"status": "no_features_returned", "feature_count": 0} for name in LAYER_TAGS}
    if with_school:
        layers["schools"] = gpd.GeoDataFrame(
            {"osm_id": ["school-1"], "amenity": ["school"]},
            geometry=[Point(27.582, 47.160)],
            crs="EPSG:4326",
        )
        availability["schools"] = {"status": "available", "feature_count": 1}
    return OSMData(
        area=area,
        graphs={"walk": graph},
        layers=layers,
        layer_availability=availability,
        metadata={
            "source": "OpenStreetMap",
            "source_version": "offline test fixture",
            "retrieved_at": "2026-10-17T00:00:00Z",
            "extent_wgs84": area.extent,
            "working_crs": area.working_crs,
            "limitations": ["synthetic test fixture; not real OSM evidence"],
        },
        warnings=[],
    )


def test_area_validation_accepts_bounded_polygon_and_bbox() -> None:
    bbox_area = normalize_area([27.58, 47.16, 27.585, 47.165])
    assert bbox_area.working_crs.startswith("EPSG:")
    assert bbox_area.boundary_source == "bounded_bbox"
    with pytest.raises(AreaValidationError, match="west, south, east, north"):
        normalize_area([27.585, 47.16, 27.58, 47.165])
    with pytest.raises(AreaValidationError, match="no larger"):
        normalize_area([27.0, 47.0, 28.0, 48.0])


def test_route_metrics_handle_connected_and_disconnected_nodes() -> None:
    graph = _fixture_data().graphs["walk"]
    route = route_between(graph, 1, 3)
    assert route["distance_m"] == 200.0
    assert route["direct_distance_m"] is not None
    assert route["detour_ratio"] > 1.0
    assert route_between(graph, 1, 4)["status"] == "unreachable"
    summary = network_metrics(graph, "walk")
    assert summary["component_count"] == 2
    assert summary["largest_component_nodes"] == 3


def test_accessibility_analysis_is_deterministic_and_json_serializable() -> None:
    data = _fixture_data()
    first = analyze_snapshot(data, access_threshold_minutes=3)
    second = analyze_snapshot(data, access_threshold_minutes=3)
    assert first["network_metrics"] == second["network_metrics"]
    assert first["analysis_id"] == second["analysis_id"]
    school_indicator = next(item for item in first["indicators"] if item["id"] == "walk_access_schools_within_3_min")
    assert school_indicator["value"] == 3
    assert any(item["type"] == "disconnected_walk_component" for item in first["issues"])
    json.dumps(first, allow_nan=False)


def test_absent_poi_layer_is_unknown_not_zero() -> None:
    result = analyze_snapshot(_fixture_data(with_school=False))
    indicator = next(item for item in result["indicators"] if item["id"] == "walk_access_schools_within_15_min")
    assert indicator["value"] is None
    assert indicator["status"] == "unknown"
    assert "not zero" in indicator["uncertainty"]["description"]


def test_virtual_connection_improves_route_without_mutating_baseline() -> None:
    data = _fixture_data(disconnected=False)
    baseline = data.graphs["walk"]
    original_edges = baseline.number_of_edges()
    result = evaluate_pedestrian_connection(data, [27.580, 47.160], [27.582, 47.160])
    assert result["comparison"]["outcome"] == "improved"
    assert result["baseline"]["network_distance_m"] == 200.0
    assert result["scenario"]["network_distance_m"] < result["baseline"]["network_distance_m"]
    assert result["comparison"]["distance_delta_m"] < 0
    assert baseline.number_of_edges() == original_edges
    assert result["baseline"]["geometry"]["type"] in {"LineString", "MultiLineString"}
    json.dumps(result, allow_nan=False)


def test_connection_can_be_disabled_and_bad_endpoints_are_rejected() -> None:
    data = _fixture_data(disconnected=False)
    start, end = [27.580, 47.160], [27.582, 47.160]
    disabled = evaluate_scenario(
        data,
        [
            {"type": "add_pedestrian_connection", "start": start, "end": end},
            {"type": "set_connection_enabled", "start": start, "end": end, "enabled": False},
        ],
        origin=start,
        destination=end,
    )
    assert disabled["comparison"]["outcome"] == "unchanged"
    with pytest.raises(InterventionError, match="inside the selected study area"):
        evaluate_pedestrian_connection(data, [27.58, 47.16], [27.70, 47.16])
    with pytest.raises(InterventionError, match="requires its start and end coordinates"):
        evaluate_scenario(
            data,
            [{"type": "set_connection_enabled", "connection_id": "arteria:unknown", "enabled": False}],
            origin=start,
            destination=end,
        )


def test_feature_collection_exports_wgs84_geojson() -> None:
    result = analyze_snapshot(_fixture_data())
    collection = result["layers"]["schools"]
    assert collection["type"] == "FeatureCollection"
    assert collection["features"][0]["geometry"]["coordinates"] == [27.582, 47.16]
    assert result["area"]["working_crs"] != "EPSG:4326"


def test_feature_collection_serializes_provider_timestamps() -> None:
    frame = gpd.GeoDataFrame(
        {"source_timestamp": [datetime(2026, 10, 17, tzinfo=timezone.utc)]},
        geometry=[Point(27.58, 47.16)],
        crs="EPSG:4326",
    )
    serialized = feature_collection(frame)
    assert serialized["features"][0]["properties"]["source_timestamp"].startswith("2026-10-17T00:00:00")
    json.dumps(serialized, allow_nan=False)


def test_osm_acquisition_uses_project_local_graph_and_feature_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"graph": 0, "features": 0}

    def fake_graph_from_polygon(*args: object, **kwargs: object) -> nx.MultiDiGraph:
        calls["graph"] += 1
        graph = nx.MultiDiGraph(crs="EPSG:4326", name="cache-test")
        graph.add_node(1, x=27.580, y=47.160)
        graph.add_node(2, x=27.581, y=47.160)
        graph.add_edge(1, 2, length=100.0, osmid=123, highway="footway")
        graph.add_edge(2, 1, length=100.0, osmid=123, highway="footway")
        return graph

    def fake_features_from_polygon(*args: object, **kwargs: object) -> gpd.GeoDataFrame:
        calls["features"] += 1
        index = pd.MultiIndex.from_tuples([("way", 456)], names=["element", "osmid"])
        return gpd.GeoDataFrame(
            {"amenity": ["school"]},
            geometry=[Point(27.5805, 47.160)],
            crs="EPSG:4326",
            index=index,
        )

    monkeypatch.setattr(geo_module.ox, "graph_from_polygon", fake_graph_from_polygon)
    monkeypatch.setattr(geo_module.ox, "features_from_polygon", fake_features_from_polygon)
    cache_root = Path(__file__).resolve().parent / ".cache"
    cache_root.mkdir(exist_ok=True)
    original_overpass_url = geo_module.ox.settings.overpass_url
    with tempfile.TemporaryDirectory(prefix="cache-test-", dir=cache_root) as temporary:
        first = acquire_osm_data([27.579, 47.159, 27.582, 47.162], modes=("walk",), cache_dir=temporary, overpass_url="https://example.invalid/api")
        assert first.graphs["walk"].number_of_edges() == 2
        assert first.layer_availability["schools"]["feature_count"] == 1
        assert first.metadata["cache"]["application_snapshot_hit"] is False

        def fail_if_requested(*args: object, **kwargs: object) -> None:
            raise AssertionError("A valid local snapshot should prevent another OSM request.")

        monkeypatch.setattr(geo_module.ox, "graph_from_polygon", fail_if_requested)
        monkeypatch.setattr(geo_module.ox, "features_from_polygon", fail_if_requested)
        second = acquire_osm_data([27.579, 47.159, 27.582, 47.162], modes=("walk",), cache_dir=temporary)
        assert second.metadata["cache"]["application_snapshot_hit"] is True
        assert second.metadata["cache"]["cached_network_modes"] == ["walk"]
        assert second.metadata["cache"]["features_cache_hit"] is True
        assert calls == {"graph": 1, "features": 1}
    assert geo_module.ox.settings.overpass_url == original_overpass_url
