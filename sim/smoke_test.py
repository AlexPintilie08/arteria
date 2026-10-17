"""Deterministic synthetic graph and geospatial import smoke checks."""

from __future__ import annotations

import geopandas
import networkx as nx
import osmnx
import shapely


def run() -> dict[str, str | int | float]:
    """Verify core imports and a small, reproducible NetworkX path calculation."""
    graph = nx.Graph()
    graph.add_weighted_edges_from(
        [("a", "b", 120.0), ("b", "c", 80.0), ("a", "c", 300.0)],
        weight="length_m",
    )
    path = nx.shortest_path(graph, "a", "c", weight="length_m")
    distance = nx.shortest_path_length(graph, "a", "c", weight="length_m")
    if path != ["a", "b", "c"] or distance != 200.0:
        raise AssertionError(f"Unexpected deterministic graph result: {path=}, {distance=}")

    return {
        "networkx": nx.__version__,
        "osmnx": osmnx.__version__,
        "geopandas": geopandas.__version__,
        "shapely": shapely.__version__,
        "shortest_path": " -> ".join(path),
        "distance_m": distance,
    }


def main() -> None:
    details = run()
    print("Spatial smoke test passed:")
    for name, value in details.items():
        print(f"  {name}: {value}")


if __name__ == "__main__":
    main()
