"""Offline tests for the geospatial pipeline and scenario engine."""

from __future__ import annotations

import json
import math
import tempfile
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import networkx as nx
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, Polygon

from sim.analysis import analyze_snapshot, network_metrics, route_between
from sim import geo as geo_module
from sim.geo import AreaValidationError, LAYER_TAGS, OSMData, OSMDataError, acquire_osm_data, feature_collection, geojson_geometry, normalize_area
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


def _network_graph(mode: str = "walk") -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph(crs="EPSG:4326", name=f"{mode}-offline-fixture")
    graph.add_node(1, x=27.580, y=47.160)
    graph.add_node(2, x=27.581, y=47.160)
    graph.add_edge(1, 2, key=0, length=100.0, osmid=123, highway="residential")
    graph.add_edge(2, 1, key=0, length=100.0, osmid=123, highway="residential")
    return graph


def _install_osm_mocks(
    monkeypatch: pytest.MonkeyPatch,
    *,
    failed_modes: set[str] | None = None,
    feature_error: Exception | None = None,
    features: gpd.GeoDataFrame | None = None,
) -> list[str]:
    requested: list[str] = []

    def fake_graph_from_polygon(*args: object, network_type: str, **kwargs: object) -> nx.MultiDiGraph:
        requested.append(network_type)
        if failed_modes and network_type in failed_modes:
            raise ConnectionError(f"fixture outage for {network_type}")
        return _network_graph(network_type)

    def fake_features_from_polygon(*args: object, **kwargs: object) -> gpd.GeoDataFrame:
        if feature_error is not None:
            raise feature_error
        if features is not None:
            return features
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    monkeypatch.setattr(geo_module.ox, "graph_from_polygon", fake_graph_from_polygon)
    monkeypatch.setattr(geo_module.ox, "features_from_polygon", fake_features_from_polygon)
    return requested


def _snapshot_with_graphs(data: OSMData, graphs: dict[str, nx.Graph]) -> OSMData:
    return OSMData(
        area=data.area,
        graphs=graphs,
        layers=data.layers,
        layer_availability=data.layer_availability,
        metadata=data.metadata,
        warnings=list(data.warnings),
    )


@pytest.fixture
def local_cache_dir() -> Iterator[Path]:
    cache_root = Path(__file__).resolve().parent / ".cache"
    cache_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="engine-test-", dir=cache_root) as temporary:
        yield Path(temporary)


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


@pytest.mark.parametrize("mode", ["walk", "drive", "bike"])
def test_acquisition_supports_each_requested_mode_independently(
    monkeypatch: pytest.MonkeyPatch,
    local_cache_dir: Path,
    mode: str,
) -> None:
    requested = _install_osm_mocks(monkeypatch)

    result = acquire_osm_data(
        [27.579, 47.159, 27.582, 47.162],
        modes=(mode,),
        cache_dir=local_cache_dir,
        use_cache=False,
    )

    assert requested == [mode]
    assert list(result.graphs) == [mode]
    assert result.metadata["requested_network_modes"] == [mode]
    assert result.layer_availability[f"{mode}_network"] == {
        "status": "available",
        "node_count": 2,
        "edge_count": 2,
    }
    assert result.warnings == []


def test_mixed_mode_acquisition_preserves_order_and_deduplicates(monkeypatch: pytest.MonkeyPatch, local_cache_dir: Path) -> None:
    modes = ("drive", "walk", "bike", "drive", "walk")
    requested = _install_osm_mocks(monkeypatch)

    result = acquire_osm_data(
        [27.579, 47.159, 27.582, 47.162],
        modes=modes,
        cache_dir=local_cache_dir,
        use_cache=False,
    )

    assert requested == ["drive", "walk", "bike"]
    assert list(result.graphs) == ["drive", "walk", "bike"]
    assert result.metadata["requested_network_modes"] == ["drive", "walk", "bike"]
    assert all(result.layer_availability[f"{mode}_network"]["status"] == "available" for mode in requested)


def test_mixed_acquisition_keeps_success_and_reports_failed_mode(monkeypatch: pytest.MonkeyPatch, local_cache_dir: Path) -> None:
    requested = _install_osm_mocks(monkeypatch, failed_modes={"bike"})

    result = acquire_osm_data(
        [27.579, 47.159, 27.582, 47.162],
        modes=("drive", "bike"),
        cache_dir=local_cache_dir,
        use_cache=False,
    )

    assert requested == ["drive", "bike"]
    assert list(result.graphs) == ["drive"]
    assert result.layer_availability["drive_network"]["status"] == "available"
    failure = result.layer_availability["bike_network"]
    assert failure["status"] == "request_failed"
    assert "fixture outage for bike" in failure["reason"]
    assert result.warnings == [failure["reason"]]


def test_complete_network_failure_raises_without_querying_features(monkeypatch: pytest.MonkeyPatch, local_cache_dir: Path) -> None:
    requested = _install_osm_mocks(monkeypatch, failed_modes={"walk", "drive"})
    feature_calls = 0

    def fail_if_feature_query(*args: object, **kwargs: object) -> gpd.GeoDataFrame:
        nonlocal feature_calls
        feature_calls += 1
        raise AssertionError("POI acquisition should not run when no requested network is available")

    monkeypatch.setattr(geo_module.ox, "features_from_polygon", fail_if_feature_query)

    with pytest.raises(OSMDataError, match="None of the requested OSM networks") as error:
        acquire_osm_data(
            [27.579, 47.159, 27.582, 47.162],
            modes=("walk", "drive"),
            cache_dir=local_cache_dir,
            use_cache=False,
        )

    assert requested == ["walk", "drive"]
    assert "fixture outage for walk" in str(error.value)
    assert "fixture outage for drive" in str(error.value)
    assert feature_calls == 0


def test_network_without_edges_is_not_reported_as_available(monkeypatch: pytest.MonkeyPatch, local_cache_dir: Path) -> None:
    _install_osm_mocks(monkeypatch)

    def empty_network(*args: object, **kwargs: object) -> nx.MultiDiGraph:
        graph = nx.MultiDiGraph(crs="EPSG:4326")
        graph.add_node(1, x=27.580, y=47.160)
        return graph

    monkeypatch.setattr(geo_module.ox, "graph_from_polygon", empty_network)

    with pytest.raises(OSMDataError, match="no routable edges"):
        acquire_osm_data(
            [27.579, 47.159, 27.582, 47.162],
            modes=("drive",),
            cache_dir=local_cache_dir,
            use_cache=False,
        )


@pytest.mark.parametrize("modes", [(), ("foot",), "walk"])
def test_acquisition_rejects_empty_unsupported_or_string_mode_selection(
    monkeypatch: pytest.MonkeyPatch,
    local_cache_dir: Path,
    modes: object,
) -> None:
    requested = _install_osm_mocks(monkeypatch)
    with pytest.raises(ValueError, match="modes|Unsupported"):
        acquire_osm_data(
            [27.579, 47.159, 27.582, 47.162],
            modes=modes,  # type: ignore[arg-type] - exercise runtime validation
            cache_dir=local_cache_dir,
            use_cache=False,
        )
    assert requested == []


def test_cached_drive_only_snapshot_is_reused_without_a_walk_graph(
    monkeypatch: pytest.MonkeyPatch,
    local_cache_dir: Path,
) -> None:
    index = pd.MultiIndex.from_tuples([("way", 456)], names=["element", "osmid"])
    schools = gpd.GeoDataFrame(
        {"amenity": ["school"]},
        geometry=[Point(27.5805, 47.160)],
        crs="EPSG:4326",
        index=index,
    )
    requested = _install_osm_mocks(monkeypatch, features=schools)
    area = [27.579, 47.159, 27.582, 47.162]
    first = acquire_osm_data(area, modes=("drive",), cache_dir=local_cache_dir)
    assert list(first.graphs) == ["drive"]
    assert first.metadata["cache"]["cached_network_modes"] == []

    def fail_if_requested(*args: object, **kwargs: object) -> None:
        raise AssertionError("A valid cached drive-only snapshot should satisfy this request")

    monkeypatch.setattr(geo_module.ox, "graph_from_polygon", fail_if_requested)
    monkeypatch.setattr(geo_module.ox, "features_from_polygon", fail_if_requested)
    second = acquire_osm_data(area, modes=("drive",), cache_dir=local_cache_dir)

    assert list(second.graphs) == ["drive"]
    assert second.metadata["cache"]["cached_network_modes"] == ["drive"]
    assert second.metadata["cache"]["features_cache_hit"] is True
    assert second.layer_availability["drive_network"]["status"] == "available"
    assert second.metadata["network_retrieved_at"]["drive"] != "unknown"
    assert second.graphs["drive"].graph["arteria_source"] == "OpenStreetMap"


def test_failed_poi_query_is_warned_and_keeps_layer_unknown(monkeypatch: pytest.MonkeyPatch, local_cache_dir: Path) -> None:
    _install_osm_mocks(monkeypatch, feature_error=TimeoutError("fixture POI timeout"))

    result = acquire_osm_data(
        [27.579, 47.159, 27.582, 47.162],
        modes=("walk",),
        cache_dir=local_cache_dir,
        use_cache=False,
    )

    assert result.layer_availability["schools"]["status"] == "unknown"
    assert any("feature request failed" in warning and "fixture POI timeout" in warning for warning in result.warnings)
    analyzed = analyze_snapshot(result)
    indicator = next(item for item in analyzed["indicators"] if item["id"] == "walk_access_schools_within_15_min")
    assert indicator["value"] is None
    assert indicator["status"] == "unknown"
    assert any("fixture POI timeout" in warning for warning in analyzed["warnings"])


def test_drive_only_analysis_does_not_invent_pedestrian_accessibility() -> None:
    data = _fixture_data()
    drive_only = _snapshot_with_graphs(data, {"drive": data.graphs["walk"]})

    result = analyze_snapshot(drive_only)

    assert set(result["network_metrics"]) == {"drive"}
    assert set(result["networks"]) == {"drive"}
    assert not any(indicator["id"].startswith(("walk_", "bike_")) for indicator in result["indicators"])
    population = next(item for item in result["indicators"] if item["id"] == "population_accessibility")
    assert population["value"] is None
    assert population["status"] == "unknown"


def test_analysis_reports_connectivity_for_only_the_available_mode() -> None:
    data = _fixture_data(disconnected=True)
    drive_only = _snapshot_with_graphs(data, {"drive": data.graphs["walk"]})

    result = analyze_snapshot(drive_only)

    assert result["network_metrics"]["drive"]["node_count"] == 4
    assert result["network_metrics"]["drive"]["component_count"] == 2
    component_indicator = next(item for item in result["indicators"] if item["id"] == "drive_network_components")
    assert component_indicator["value"] == 2
    assert any(issue["type"] == "disconnected_drive_component" for issue in result["issues"])


def test_projected_geojson_preserves_wgs84_crs_and_longitude_latitude_order() -> None:
    original = gpd.GeoDataFrame(
        {"kind": ["marker"]},
        geometry=[Point(27.58, 47.16)],
        crs="EPSG:4326",
    )
    projected = original.to_crs("EPSG:3857")

    collection = feature_collection(projected)
    geometry = geojson_geometry(projected.geometry.iloc[0], "EPSG:3857")

    coordinates = collection["features"][0]["geometry"]["coordinates"]
    assert coordinates[0] == pytest.approx(27.58, abs=1e-6)
    assert coordinates[1] == pytest.approx(47.16, abs=1e-6)
    assert geometry["type"] == "Point"
    assert geometry["coordinates"] == pytest.approx([27.58, 47.16], abs=1e-6)


def test_analysis_and_scenario_outputs_are_json_finite_and_geojson_valid() -> None:
    data = _fixture_data()
    analysis = analyze_snapshot(data)
    scenario = evaluate_pedestrian_connection(data, [27.580, 47.160], [27.582, 47.160])

    json.dumps(analysis, allow_nan=False)
    json.dumps(scenario, allow_nan=False)
    assert analysis["area"]["crs"] == "EPSG:4326"
    assert analysis["layers"]["schools"]["type"] == "FeatureCollection"
    assert analysis["networks"]["walk"]["type"] == "FeatureCollection"
    assert analysis["issue_geojson"]["type"] == "FeatureCollection"
    assert scenario["baseline"]["geometry"]["type"] == "LineString"
    assert scenario["scenario"]["geometry"]["type"] == "LineString"
    for route in (scenario["baseline"], scenario["scenario"]):
        longitude, latitude = route["geometry"]["coordinates"][0]
        assert -180 <= longitude <= 180
        assert -90 <= latitude <= 90


def _graph_fingerprint(graph: nx.Graph) -> str:
    nodes = sorted((repr(node), repr(sorted(attrs.items()))) for node, attrs in graph.nodes(data=True))
    if graph.is_multigraph():
        edges = sorted((repr(u), repr(v), repr(key), repr(sorted(attrs.items()))) for u, v, key, attrs in graph.edges(keys=True, data=True))
    else:
        edges = sorted((repr(u), repr(v), "", repr(sorted(attrs.items()))) for u, v, attrs in graph.edges(data=True))
    return repr((sorted(graph.graph.items()), nodes, edges))


def test_scenario_is_deterministic_and_never_mutates_baseline_graph() -> None:
    data = _fixture_data(disconnected=False)
    baseline = data.graphs["walk"]
    original = _graph_fingerprint(baseline)
    args = (data, [
        {"type": "add_pedestrian_connection", "start": [27.580, 47.160], "end": [27.582, 47.160]},
    ])
    kwargs = {"origin": [27.580, 47.160], "destination": [27.582, 47.160], "walking_speed_mps": 2.0}

    first = evaluate_scenario(*args, **kwargs)
    second = evaluate_scenario(*args, **kwargs)

    assert first == second
    assert _graph_fingerprint(baseline) == original
    assert first["comparison"]["outcome"] == "improved"
    assert first["scenario"]["estimated_walk_time_s"] == pytest.approx(first["scenario"]["network_distance_m"] / 2.0)
    assert first["interventions"][0]["estimated_walk_time_s"] == pytest.approx(first["interventions"][0]["connection_length_m"] / 2.0)
    assert first["provenance"]["source"] == "OpenStreetMap"
    assert any("hypothetical" in warning for warning in first["warnings"])


def test_scenario_can_represent_a_regression_when_a_connection_is_disabled() -> None:
    data = _fixture_data(disconnected=False)
    start, end = [27.580, 47.160], [27.582, 47.160]
    added = evaluate_pedestrian_connection(data, start, end)
    descriptor = added["interventions"][0]
    connection_id = descriptor["connection_id"]
    graph = data.graphs["walk"]
    line = LineString([(graph.nodes[1]["x"], graph.nodes[1]["y"]), (graph.nodes[3]["x"], graph.nodes[3]["y"])])
    edge_attrs = {
        "length": descriptor["connection_length_m"],
        "length_m": descriptor["connection_length_m"],
        "geometry": line,
        "arteria_virtual_id": connection_id,
    }
    graph.add_edge(1, 3, key=f"{connection_id}:forward", **edge_attrs)
    graph.add_edge(3, 1, key=f"{connection_id}:reverse", **edge_attrs)

    result = evaluate_scenario(
        data,
        [{"type": "set_connection_enabled", "connection_id": connection_id, "enabled": False}],
        origin=start,
        destination=end,
    )

    assert result["comparison"]["outcome"] == "regressed"
    assert result["comparison"]["distance_delta_m"] > 0
    assert result["baseline"]["network_distance_m"] < result["scenario"]["network_distance_m"]


def test_scenario_reports_when_an_intervention_makes_a_route_reachable() -> None:
    data = _fixture_data(disconnected=True)

    result = evaluate_pedestrian_connection(data, [27.580, 47.160], [27.585, 47.160])

    assert result["baseline"]["status"] == "unreachable"
    assert result["scenario"]["status"] == "reachable"
    assert result["comparison"]["outcome"] == "became_reachable"
    assert result["comparison"]["distance_delta_m"] is None


def test_scenario_rejects_endpoints_that_cannot_snap_within_the_distance_limit() -> None:
    data = _fixture_data()

    with pytest.raises(InterventionError, match="beyond the 50 m snap limit"):
        evaluate_pedestrian_connection(data, [27.580, 47.160], [27.587, 47.168])


def test_scenario_rejects_links_longer_than_the_configured_maximum() -> None:
    data = _fixture_data(disconnected=False)
    graph = data.graphs["walk"]
    graph.add_node(5, x=27.589, y=47.169)
    graph.add_edge(1, 5, key=0, length=10.0, length_m=10.0)
    graph.add_edge(5, 1, key=0, length=10.0, length_m=10.0)

    with pytest.raises(InterventionError, match="no longer than 1000 m"):
        evaluate_pedestrian_connection(data, [27.580, 47.160], [27.589, 47.169])


def test_non_finite_analysis_and_scenario_parameters_are_rejected() -> None:
    data = _fixture_data()
    with pytest.raises(ValueError, match="finite"):
        analyze_snapshot(data, access_threshold_minutes=math.nan)
    with pytest.raises(InterventionError, match="finite and positive"):
        evaluate_scenario(
            data,
            [],
            origin=[27.580, 47.160],
            destination=[27.582, 47.160],
            walking_speed_mps=math.inf,
        )
