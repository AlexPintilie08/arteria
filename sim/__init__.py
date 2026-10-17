"""Spatial analysis and optional simulation utilities."""
"""Geospatial analysis and scenario APIs for ARTERIA."""

from .analysis import analyze_area, analyze_snapshot, network_metrics, normalize_graph, project_graph, route_between
from .geo import AreaValidationError, OSMData, OSMDataError, StudyArea, acquire_osm_data, feature_collection, normalize_area
from .neighborhoods import (
    NeighborhoodCatalogError,
    get_neighborhood,
    get_neighborhoods,
    load_neighborhood_catalog,
    neighborhood_area_input,
    neighborhoods_geojson,
    search_neighborhoods,
    validate_neighborhood_boundary,
)
from .candidates import discover_intervention_candidates
from .impact import evaluate_candidates, evaluate_multi_route_impact, sample_route_pairs
from .scenario import InterventionError, evaluate_pedestrian_connection, evaluate_scenario

__all__ = [
    "AreaValidationError",
    "InterventionError",
    "NeighborhoodCatalogError",
    "OSMData",
    "OSMDataError",
    "StudyArea",
    "acquire_osm_data",
    "analyze_area",
    "analyze_snapshot",
    "evaluate_pedestrian_connection",
    "evaluate_scenario",
    "evaluate_candidates",
    "evaluate_multi_route_impact",
    "discover_intervention_candidates",
    "feature_collection",
    "get_neighborhood",
    "get_neighborhoods",
    "load_neighborhood_catalog",
    "neighborhood_area_input",
    "neighborhoods_geojson",
    "network_metrics",
    "normalize_area",
    "normalize_graph",
    "project_graph",
    "route_between",
    "sample_route_pairs",
    "search_neighborhoods",
    "validate_neighborhood_boundary",
]
