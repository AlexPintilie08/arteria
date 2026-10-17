from sim.smoke_test import run


def test_synthetic_network_result_is_deterministic() -> None:
    result = run()
    assert result["shortest_path"] == "a -> b -> c"
    assert result["distance_m"] == 200.0
    assert result["osmnx"]
    assert result["geopandas"]
    assert result["shapely"]
