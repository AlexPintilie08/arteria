"""Spatial analysis and optional simulation utilities."""
"""Geospatial analysis and scenario APIs for ARTERIA."""

from .analysis import analyze_area, analyze_snapshot, network_metrics, normalize_graph, project_graph, route_between
from .geo import AreaValidationError, OSMData, OSMDataError, StudyArea, acquire_osm_data, feature_collection, normalize_area
from .scenario import InterventionError, evaluate_pedestrian_connection, evaluate_scenario

__all__ = [
    "AreaValidationError",
    "InterventionError",
    "OSMData",
    "OSMDataError",
    "StudyArea",
    "acquire_osm_data",
    "analyze_area",
    "analyze_snapshot",
    "evaluate_pedestrian_connection",
    "evaluate_scenario",
    "feature_collection",
    "network_metrics",
    "normalize_area",
    "normalize_graph",
    "project_graph",
    "route_between",
]
