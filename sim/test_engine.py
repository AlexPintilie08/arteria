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
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, mapping, shape

from sim.analysis import analyze_snapshot, network_metrics, route_between
from sim import geo as geo_module
from sim.geo import AreaValidationError, LAYER_TAGS, OSMData, OSMDataError, acquire_osm_data, feature_collection, geojson_geometry, normalize_area
from sim.scenario import InterventionError, evaluate_pedestrian_connection, evaluate_scenario
from sim.candidates import _feature_intersections, _prepare_feature_index, discover_intervention_candidates
from sim.impact import evaluate_candidates, evaluate_multi_route_impact, sample_route_pairs
from sim.neighborhoods import (
    NeighborhoodCatalogError,
    get_neighborhood,
    get_neighborhoods,
    load_neighborhood_catalog,
    neighborhood_area_input,
    neighborhoods_geojson,
    search_neighborhoods,
    validate_neighborhood_boundary,
)


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
        graph_sidecar = next(Path(temporary).glob("*-walk.json"))
        feature_sidecar = next(Path(temporary).glob("*-features.json"))
        graph_metadata = json.loads(graph_sidecar.read_text(encoding="utf-8"))
        feature_metadata = json.loads(feature_sidecar.read_text(encoding="utf-8"))
        assert graph_metadata["source_area_geometry_sha256"] == first.metadata["source_area_geometry_sha256"]
        assert graph_metadata["source_area_geometry"]["type"] == "Polygon"
        assert graph_metadata["query"]["network_type"] == "walk"
        assert feature_metadata["source_area_geometry_sha256"] == first.metadata["source_area_geometry_sha256"]
        assert feature_metadata["query"]["tags"]["building"] is True

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


# SIM engine v2 regression coverage


def _geojson_feature(identifier: str, name: str, geometry: dict, **properties: object) -> dict:
    return {
        "type": "Feature",
        "id": identifier,
        "geometry": geometry,
        "properties": {"neighborhood_id": identifier, "name": name, "source": "test source", "source_object_id": identifier, **properties},
    }


def test_neighborhood_catalog_loads_sourced_polygons_and_point_only_records() -> None:
    records = get_neighborhoods()
    polygons = [record for record in records if record["geometry_type"] in {"Polygon", "MultiPolygon"}]
    points = [record for record in records if record["geometry_type"] == "Point"]

    assert len(polygons) == 24
    assert len(points) == 7
    assert all(record["provenance"]["license"] == "ODbL-1.0" for record in records)
    assert all(record["boundary_status"] != "official" for record in polygons)
    assert all(record["boundary_status"] == "point_only" for record in points)
    assert get_neighborhood(points[0]["id"])["id"] == points[0]["id"]
    assert search_neighborhoods("Tatarasi")


def test_neighborhood_polygon_validation_and_analysis_input() -> None:
    record = next(record for record in get_neighborhoods() if record["geometry_type"] == "Polygon")

    validation = validate_neighborhood_boundary(record)
    area_input = neighborhood_area_input(record)

    assert validation["status"] == "valid"
    assert validation["analysis_eligible"] is True
    assert validation["area_km2"] > 0
    assert normalize_area(area_input).boundary_source.startswith("catalog:")


def test_neighborhood_multipolygon_import_is_preserved() -> None:
    west, south = 27.58, 47.16
    first = Polygon([(west, south), (west + 0.0002, south), (west + 0.0002, south + 0.0002), (west, south + 0.0002), (west, south)])
    second = Polygon([(west + 0.001, south), (west + 0.0012, south), (west + 0.0012, south + 0.0002), (west + 0.001, south + 0.0002), (west + 0.001, south)])
    feature = _geojson_feature("multi-1", "Two mapped pieces", {"type": "MultiPolygon", "coordinates": [[list(first.exterior.coords)], [list(second.exterior.coords)]]})

    record = load_neighborhood_catalog([feature])[0]
    validation = validate_neighborhood_boundary(record)

    assert record["geometry_type"] == "MultiPolygon"
    assert validation["status"] == "valid"
    assert shape(record["geometry"]).geom_type == "MultiPolygon"


def test_neighborhood_catalog_rejects_invalid_geometry_and_crs() -> None:
    bowtie = {"type": "Polygon", "coordinates": [[[27.58, 47.16], [27.582, 47.162], [27.582, 47.16], [27.58, 47.162], [27.58, 47.16]]]}
    with pytest.raises(NeighborhoodCatalogError, match="invalid geometry"):
        load_neighborhood_catalog([_geojson_feature("bad", "Invalid", bowtie)])

    valid = _geojson_feature("crs", "Wrong CRS", mapping(_fixture_data().area.polygon))
    with pytest.raises(NeighborhoodCatalogError, match="EPSG:4326"):
        load_neighborhood_catalog({"type": "FeatureCollection", "metadata": {"coordinate_reference_system": "EPSG:3857"}, "features": [valid]})


def test_point_only_neighborhood_never_becomes_an_analysis_area() -> None:
    point = _geojson_feature("point-1", "Named place", {"type": "Point", "coordinates": [27.58, 47.16]}, boundary_status="point_only")
    record = load_neighborhood_catalog([point])[0]

    validation = validate_neighborhood_boundary(record)

    assert validation["status"] == "point_only"
    assert validation["analysis_eligible"] is False
    with pytest.raises(AreaValidationError, match="no neighborhood boundary"):
        neighborhood_area_input(record)


def test_missing_neighborhood_provenance_is_explicitly_marked() -> None:
    polygon = _geojson_feature("unprovenanced", "Imported area", mapping(_fixture_data().area.polygon))
    record = load_neighborhood_catalog([polygon])[0]

    assert record["source_object_id"] == "unprovenanced"
    assert record["retrieved_at"] is None
    assert record["provenance"]["source"] == "test source"
    assert record["uncertainty_notes"]


def test_oversized_neighborhood_requires_explicit_controlled_limits() -> None:
    large = Polygon([(27.50, 47.10), (27.60, 47.10), (27.60, 47.20), (27.50, 47.20), (27.50, 47.10)])
    record = _geojson_feature("large", "Large area", mapping(large))

    standard = validate_neighborhood_boundary(record)
    controlled = validate_neighborhood_boundary(record, max_area_km2=100, max_extent_km=20)

    assert standard["status"] == "requires_controlled_analysis"
    assert standard["analysis_eligible"] is False
    assert controlled["status"] == "valid"
    assert neighborhood_area_input(record, max_area_km2=100, max_extent_km=20)["area_id"] == "large"


def test_neighborhood_geojson_serialization_is_stable() -> None:
    first = neighborhoods_geojson()
    second = neighborhoods_geojson()

    assert json.dumps(first, ensure_ascii=False, sort_keys=True, allow_nan=False) == json.dumps(second, ensure_ascii=False, sort_keys=True, allow_nan=False)
    assert first["type"] == "FeatureCollection"
    assert len(first["features"]) == 31


def test_candidate_discovery_finds_disconnected_nodes_with_stable_supported_output() -> None:
    data = _fixture_data(disconnected=True)
    issues = analyze_snapshot(data)["issues"]

    first = discover_intervention_candidates(data, issues=issues)
    second = discover_intervention_candidates(data, issues=issues)

    assert first == second
    assert first["candidates"]
    assert all(candidate["intervention"]["type"] == "add_pedestrian_connection" for candidate in first["candidates"])
    assert all(candidate["geometry"]["type"] == "LineString" for candidate in first["candidates"])
    assert all(candidate["screening"]["physical_feasibility"] == "unknown" for candidate in first["candidates"])
    assert all(candidate["candidate_generation_method_version"] == first["method_version"] for candidate in first["candidates"])
    json.dumps(first, ensure_ascii=False, allow_nan=False)


def test_candidate_discovery_detects_a_large_connected_route_detour() -> None:
    data = _fixture_data(disconnected=False)
    for _, _, _, attrs in data.graphs["walk"].edges(keys=True, data=True):
        attrs["length_m"] = attrs["length"] = 600.0

    report = discover_intervention_candidates(data, max_candidates=10)

    assert any(candidate["discovery"]["method"] == "excessive_route_detour" for candidate in report["candidates"])
    assert all(candidate["discovery"]["detour_ratio"] > 2.0 for candidate in report["candidates"] if candidate["discovery"]["method"] == "excessive_route_detour")


def test_candidate_discovery_skips_existing_direct_connections_and_duplicates() -> None:
    data = _fixture_data(disconnected=False)
    graph = data.graphs["walk"]
    graph.add_edge(1, 3, key=0, length=50.0, length_m=50.0)
    graph.add_edge(3, 1, key=0, length=50.0, length_m=50.0)
    no_opportunity = discover_intervention_candidates(data, max_candidates=10)
    assert no_opportunity["candidates"] == []
    assert no_opportunity["screening"]["rejected"]["already_directly_connected"] > 0

    duplicate_data = _fixture_data(disconnected=True)
    duplicate_data.graphs["walk"].add_node(5, x=27.58501, y=47.160)
    deduplicated = discover_intervention_candidates(duplicate_data, max_candidates=10)
    assert deduplicated["screening"]["rejected"].get("functionally_equivalent_candidate", 0) > 0


def test_candidate_discovery_respects_maximum_length_and_study_area() -> None:
    bounded = discover_intervention_candidates(_fixture_data(disconnected=True), max_connection_length_m=50)
    assert all(candidate["length_m"] <= 50 for candidate in bounded["candidates"])

    first = Polygon([(27.57565, 47.1599), (27.57595, 47.1599), (27.57595, 47.1601), (27.57565, 47.1601), (27.57565, 47.1599)])
    second = Polygon([(27.57795, 47.1599), (27.57825, 47.1599), (27.57825, 47.1601), (27.57795, 47.1601), (27.57795, 47.1599)])
    area = normalize_area({"area_id": "two-islands", "boundary": MultiPolygon([first, second]), "crs": "EPSG:4326"})
    graph = nx.MultiDiGraph(crs="EPSG:4326")
    graph.add_node(1, x=27.5758, y=47.1600)
    graph.add_node(2, x=27.5781, y=47.1600)
    graph.add_node(3, x=27.5770, y=47.1600)
    for left, right in ((1, 3), (3, 2)):
        graph.add_edge(left, right, length=500.0, length_m=500.0)
        graph.add_edge(right, left, length=500.0, length_m=500.0)
    base = _fixture_data(disconnected=False)
    outside_line_data = OSMData(area, {"walk": graph}, base.layers, base.layer_availability, base.metadata, [])
    outside_line_report = discover_intervention_candidates(outside_line_data, max_candidates=10)
    assert outside_line_report["candidates"] == []
    assert outside_line_report["screening"]["rejected"].get("outside_study_polygon", 0) > 0


def test_candidate_discovery_flags_mapped_buildings_and_missing_feasibility_evidence() -> None:
    data = _fixture_data(disconnected=True)
    building = Polygon([(27.5833, 47.15999), (27.5837, 47.15999), (27.5837, 47.16001), (27.5833, 47.16001), (27.5833, 47.15999)])
    data.layers["buildings"] = gpd.GeoDataFrame({"osm_id": ["building-1"]}, geometry=[building], crs="EPSG:4326")
    data.layer_availability["buildings"] = {"status": "available", "feature_count": 1}

    report = discover_intervention_candidates(data, max_candidates=1)
    assert report["candidates"] == []
    assert report["screening"]["candidate_pool_count"] > 1
    assert report["screening"]["candidate_count_rejected_material_conflict"] > 0
    candidate = report["screened_candidates"][0]

    assert candidate["screening"]["mapped_buildings"]["status"] == "mapped_obstacle_intersection"
    assert candidate["screening"]["mapped_buildings"]["classification"] == "mapped_material_conflict"
    assert candidate["screening"]["eligibility"] == "blocked"
    assert candidate["screening"]["mapped_buildings"]["feature_ids"] == ["building-1"]
    assert candidate["screening"]["physical_feasibility"] == "unknown"
    assert "land ownership and access rights" in candidate["screening"]["missing_evidence"]


def test_building_screening_distinguishes_material_crossing_endpoint_boundary_and_short_overlap() -> None:
    data = _fixture_data(disconnected=False)
    line = LineString([(27.580, 47.160), (27.585, 47.160)])

    def screen(geometry: object) -> dict[str, object]:
        data.layers["buildings"] = gpd.GeoDataFrame({"osm_id": ["b-1"]}, geometry=[geometry], crs="EPSG:4326")
        data.layer_availability["buildings"] = {"status": "available", "feature_count": 1}
        return _feature_intersections(_prepare_feature_index(data, "buildings"), line)

    interior = screen(Polygon([(27.582, 47.1599), (27.583, 47.1599), (27.583, 47.1601), (27.582, 47.1601), (27.582, 47.1599)]))
    assert interior["classification"] == "mapped_material_conflict"
    assert interior["intersections"][0]["classification"] == "interior_crossing"
    assert interior["intersections"][0]["interior_overlap_m"] > 0.5

    endpoint = screen(Polygon([(27.5799, 47.1599), (27.5805, 47.1599), (27.5805, 47.1601), (27.5799, 47.1601), (27.5799, 47.1599)]))
    assert endpoint["intersections"][0]["classification"] == "endpoint_inside"

    metric_line = gpd.GeoSeries([line], crs="EPSG:4326").to_crs(data.area.working_crs).iloc[0]
    (x1, y1), (x2, y2) = list(metric_line.coords)
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    nx, ny = -dy / length * 5, dx / length * 5
    metric_boundary = Polygon([(x1, y1), (x2, y2), (x2 + nx, y2 + ny), (x1 + nx, y1 + ny), (x1, y1)])
    boundary = screen(gpd.GeoSeries([metric_boundary], crs=data.area.working_crs).to_crs("EPSG:4326").iloc[0])
    assert boundary["status"] == "conditional_review"
    assert boundary["intersections"][0]["classification"] == "boundary_only_contact"

    short = screen(Polygon([(27.582, 47.1599), (27.582002, 47.1599), (27.582002, 47.1601), (27.582, 47.1601), (27.582, 47.1599)]))
    assert short["status"] == "conditional_review"
    assert short["intersections"][0]["classification"] == "short_interior_overlap_requires_review"


def test_building_screening_deduplicates_osm_identity_and_reports_multipolygon_and_bad_features() -> None:
    data = _fixture_data(disconnected=False)
    polygon = Polygon([(27.582, 47.1599), (27.583, 47.1599), (27.583, 47.1601), (27.582, 47.1601), (27.582, 47.1599)])
    multipart = MultiPolygon([polygon, Polygon([(27.584, 47.1599), (27.5845, 47.1599), (27.5845, 47.1601), (27.584, 47.1601), (27.584, 47.1599)])])
    metric_line = gpd.GeoSeries([LineString([(27.580, 47.160), (27.585, 47.160)])], crs="EPSG:4326").to_crs(data.area.working_crs).iloc[0]
    point_on_line = gpd.GeoSeries([Point(metric_line.interpolate(0.9, normalized=True))], crs=data.area.working_crs).to_crs("EPSG:4326").iloc[0]
    data.layers["buildings"] = gpd.GeoDataFrame(
        {"osm_id": ["duplicate", "duplicate", "point"]},
        geometry=[multipart, multipart, point_on_line],
        crs="EPSG:4326",
    )
    data.layer_availability["buildings"] = {"status": "available", "feature_count": 3}

    result = _feature_intersections(_prepare_feature_index(data, "buildings"), LineString([(27.580, 47.160), (27.585, 47.160)]))

    assert result["status"] == "mapped_obstacle_intersection"
    assert result["quality"]["duplicate_record_count"] == 1
    assert result["quality"]["nonpolygon_geometry_count"] == 1
    assert result["intersection_count"] == 2
    assert result["classification_counts"]["ambiguous_invalid_feature"] == 1
    assert result["classification_counts"]["interior_crossing"] == 1


def test_unmatched_legacy_cache_cannot_claim_no_building_intersection() -> None:
    data = _fixture_data(disconnected=False)
    data.metadata["cache"] = {"area_key_matches": False, "area_equivalence_verified": False}
    data.layers["buildings"] = gpd.GeoDataFrame({"osm_id": ["b-away"]}, geometry=[Point(27.589, 47.169)], crs="EPSG:4326")
    data.layer_availability["buildings"] = {"status": "available", "feature_count": 1}

    result = _feature_intersections(_prepare_feature_index(data, "buildings"), LineString([(27.580, 47.160), (27.585, 47.160)]))

    assert result["classification"] == "unknown_source_area_unverified"
    assert result["status"] == "unknown_source_area_unverified"


def test_candidate_pool_screens_before_shortlist_and_can_return_a_clean_alternative() -> None:
    data = _fixture_data(disconnected=True)
    graph = data.graphs["walk"]
    graph.add_node(5, x=27.584, y=47.161)
    building = Polygon([(27.5833, 47.15999), (27.5837, 47.15999), (27.5837, 47.16001), (27.5833, 47.16001), (27.5833, 47.15999)])
    data.layers["buildings"] = gpd.GeoDataFrame({"osm_id": ["crossing-building"]}, geometry=[building], crs="EPSG:4326")
    data.layer_availability["buildings"] = {"status": "available", "feature_count": 1}

    report = discover_intervention_candidates(data, max_candidates=1, candidate_pool_limit=50)

    assert len(report["candidates"]) == 1
    assert report["screening"]["candidate_count_screened"] > report["screening"]["candidate_count_returned"]
    assert report["screened_candidates"]
    assert report["candidates"][0]["screening"]["eligibility"] == "conditional"
    assert all(candidate["screening"]["eligibility"] == "blocked" for candidate in report["screened_candidates"])


def test_candidate_evaluation_returns_honest_empty_result_when_screening_blocks_the_pool() -> None:
    data = _fixture_data(disconnected=True)
    area_polygon = Polygon([(27.575, 47.155), (27.590, 47.155), (27.590, 47.170), (27.575, 47.170), (27.575, 47.155)])
    data.layers["buildings"] = gpd.GeoDataFrame({"osm_id": ["covers-area"]}, geometry=[area_polygon], crs="EPSG:4326")
    data.layer_availability["buildings"] = {"status": "available", "feature_count": 1}

    result = evaluate_candidates(data, sample_count=8)

    assert result["ranked_candidates"] == []
    assert result["recommendations"] == []
    assert result["sample"]["kind"] == "not_created"
    assert result["candidate_discovery"]["candidate_count_rejected_material_conflict"] > 0
    assert "No eligible candidate" in result["recommendation_status"]


def test_candidate_discovery_returns_an_honest_empty_result_without_walking_graph() -> None:
    data = _fixture_data()

    report = discover_intervention_candidates(_snapshot_with_graphs(data, {}))

    assert report["candidates"] == []
    assert report["screening"]["reason"] == "missing_walking_graph"


def test_candidate_discovery_skips_nonfinite_nodes_and_marks_missing_buildings_unknown() -> None:
    data = _fixture_data(disconnected=True)
    data.graphs["walk"].add_node(99, x=math.nan, y=47.160)
    data.layers.pop("buildings", None)
    data.layer_availability.pop("buildings", None)

    report = discover_intervention_candidates(data)

    assert report["candidates"]
    assert all("99" not in {candidate["start"]["node_id"], candidate["end"]["node_id"]} for candidate in report["candidates"])
    assert all(candidate["screening"]["mapped_buildings"]["status"] == "unknown" for candidate in report["candidates"])


def test_impact_engine_classifies_improved_unchanged_and_newly_reachable_routes() -> None:
    data = _fixture_data(disconnected=True)
    intervention = {"type": "add_pedestrian_connection", "start": [27.582, 47.160], "end": [27.585, 47.160]}

    result = evaluate_multi_route_impact(data, [intervention], route_pairs=[(1, 3), (1, 4), (2, 4)])

    assert result["aggregate"]["unchanged_count"] == 1
    assert result["aggregate"]["newly_reachable_count"] == 2
    assert result["aggregate"]["improved_count"] == 0
    assert result["aggregate"]["reachable_both_comparable_pair_count"] == 1
    assert result["aggregate"]["total_distance_savings_m"] == pytest.approx(0)
    assert {route["outcome"] for route in result["routes"]} == {"unchanged", "newly_reachable"}
    json.dumps(result, allow_nan=False)


def test_explicit_route_pairs_preserve_both_directions() -> None:
    pairs = sample_route_pairs(_fixture_data(disconnected=True), route_pairs=[(1, 2), (2, 1), (1, 2)])

    assert pairs == [(1, 2), (2, 1)]


def test_impact_engine_measures_improvement_and_caps_route_geometry_only() -> None:
    data = _fixture_data(disconnected=False)
    intervention = {"type": "add_pedestrian_connection", "start": [27.580, 47.160], "end": [27.582, 47.160]}

    result = evaluate_multi_route_impact(data, [intervention], route_pairs=[(1, 3), (1, 2)], route_geometry_limit=1, walking_speed_mps=2.0)

    assert result["routes"][0]["outcome"] == "improved"
    assert result["routes"][0]["after"]["estimated_walk_time_s"] == pytest.approx(result["routes"][0]["after"]["network_distance_m"] / 2.0)
    assert result["configuration"]["route_geometries_included_count"] <= 1
    assert sum(
        int(route["before"]["geometry_included"]) + int(route["after"]["geometry_included"])
        for route in result["routes"]
    ) <= 1
    assert result["aggregate"]["evaluated_pair_count"] == 2
    assert result["aggregate"]["improved_count"] == 1


def test_route_sampler_is_stable_bounded_and_validates_explicit_pairs() -> None:
    data = _fixture_data(disconnected=True)
    first = sample_route_pairs(data, sample_count=6, seed="sample-a")
    second = sample_route_pairs(data, sample_count=6, seed="sample-a")

    assert first == second
    assert len(first) == 6
    assert all(origin != destination for origin, destination in first)
    with pytest.raises(ValueError, match="unknown walking graph node"):
        sample_route_pairs(data, route_pairs=[(1, "missing")])


def test_impact_results_are_repeatable_and_preserve_the_baseline_graph() -> None:
    data = _fixture_data(disconnected=True)
    baseline = data.graphs["walk"]
    fingerprint = _graph_fingerprint(baseline)
    intervention = {"type": "add_pedestrian_connection", "start": [27.582, 47.160], "end": [27.585, 47.160]}
    args = (data, [intervention])
    kwargs = {"route_pairs": [(1, 4), (2, 4)], "seed": "stable"}

    first = evaluate_multi_route_impact(*args, **kwargs)
    second = evaluate_multi_route_impact(*args, **kwargs)

    assert first == second
    assert _graph_fingerprint(baseline) == fingerprint


def test_independent_alternatives_start_from_the_same_baseline() -> None:
    data = _fixture_data(disconnected=True)
    first = evaluate_multi_route_impact(
        data,
        [{"type": "add_pedestrian_connection", "start": [27.580, 47.160], "end": [27.582, 47.160]}],
        route_pairs=[(1, 4)],
    )
    second = evaluate_multi_route_impact(
        data,
        [{"type": "add_pedestrian_connection", "start": [27.582, 47.160], "end": [27.585, 47.160]}],
        route_pairs=[(1, 4)],
    )

    assert first["routes"][0]["before"]["status"] == second["routes"][0]["before"]["status"] == "unreachable"
    assert first["routes"][0]["after"]["status"] == "unreachable"
    assert second["routes"][0]["after"]["status"] == "reachable"


def test_impact_engine_classifies_regression_and_newly_unreachable_routes() -> None:
    connected = _fixture_data(disconnected=False)
    start, end = [27.580, 47.160], [27.582, 47.160]
    enabled = evaluate_pedestrian_connection(connected, start, end)["interventions"][0]
    connected_line = LineString([(27.580, 47.160), (27.582, 47.160)])
    edge_attrs = {
        "arteria_virtual_id": enabled["connection_id"],
        "length": enabled["connection_length_m"],
        "length_m": enabled["connection_length_m"],
        "geometry": connected_line,
    }
    connected.graphs["walk"].add_edge(1, 3, key=f"{enabled['connection_id']}:forward", **edge_attrs)
    connected.graphs["walk"].add_edge(3, 1, key=f"{enabled['connection_id']}:reverse", **edge_attrs)
    regressed = evaluate_multi_route_impact(
        connected,
        [{"type": "set_connection_enabled", "connection_id": enabled["connection_id"], "enabled": False}],
        route_pairs=[(1, 3)],
    )

    disconnected = _fixture_data(disconnected=True)
    bridge = evaluate_pedestrian_connection(disconnected, [27.582, 47.160], [27.585, 47.160])["interventions"][0]
    bridge_line = LineString([(27.582, 47.160), (27.585, 47.160)])
    bridge_attrs = {
        "arteria_virtual_id": bridge["connection_id"],
        "length": bridge["connection_length_m"],
        "length_m": bridge["connection_length_m"],
        "geometry": bridge_line,
    }
    disconnected.graphs["walk"].add_edge(3, 4, key=f"{bridge['connection_id']}:forward", **bridge_attrs)
    disconnected.graphs["walk"].add_edge(4, 3, key=f"{bridge['connection_id']}:reverse", **bridge_attrs)
    newly_unreachable = evaluate_multi_route_impact(
        disconnected,
        [{"type": "set_connection_enabled", "connection_id": bridge["connection_id"], "enabled": False}],
        route_pairs=[(1, 4)],
    )

    assert regressed["routes"][0]["outcome"] == "regressed"
    assert regressed["aggregate"]["regressed_count"] == 1
    assert newly_unreachable["routes"][0]["outcome"] == "newly_unreachable"
    assert newly_unreachable["aggregate"]["newly_unreachable_count"] == 1


def test_impact_aggregates_are_null_when_no_two_reachable_routes_can_be_compared() -> None:
    result = evaluate_multi_route_impact(_fixture_data(disconnected=True), [], route_pairs=[(1, 4)])

    assert result["aggregate"]["unreachable_in_both_count"] == 1
    assert result["aggregate"]["reachable_both_comparable_pair_count"] == 0
    assert result["aggregate"]["total_distance_savings_m"] is None
    assert result["aggregate"]["average_distance_savings_m"] is None
    assert result["aggregate"]["improvement_percent"] is None
    json.dumps(result, allow_nan=False)


def test_candidate_pipeline_uses_one_shared_non_discovery_sample_and_stable_ranking() -> None:
    data = _fixture_data(disconnected=True)

    first = evaluate_candidates(data, sample_count=8, seed="ranking")
    second = evaluate_candidates(data, sample_count=8, seed="ranking")

    assert first == second
    ranked = first["ranked_candidates"]
    assert ranked
    assert [item["rank"] for item in ranked] == list(range(1, len(ranked) + 1))
    samples = [item["impact"]["sample"] for item in ranked]
    assert all(sample == samples[0] for sample in samples)
    discovery_pairs = {
        frozenset((candidate["start"]["node_id"], candidate["end"]["node_id"]))
        for candidate in ranked
    }
    evaluated_pairs = {
        frozenset((route["origin_node_id"], route["destination_node_id"]))
        for route in ranked[0]["impact"]["routes"]
    }
    assert not discovery_pairs.intersection(evaluated_pairs)
    assert "Lexicographic" in first["ranking_rule"]
    assert first["recommendations"] == []
    assert all(candidate["targeted_diagnostic_impact"]["sample"]["kind"] == "targeted_diagnostic_routes" for candidate in ranked)
    assert all(candidate["targeted_diagnostic_impact"]["sample"]["evaluated_pair_count"] <= 32 for candidate in ranked)
    assert all(candidate["ranking_explanation"].find("excluded from ranking") >= 0 for candidate in ranked)
