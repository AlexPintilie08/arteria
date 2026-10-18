"""Spatial analysis and optional simulation utilities."""
"""Geospatial analysis and scenario APIs for ARTERIA."""

from importlib import import_module

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
from .proposal_catalog import INTERVENTION_CATALOG_VERSION, get_intervention_catalog
from .proposal_context import build_proposal_context
from .proposal_validation import validate_proposal, validate_proposal_set
from .proposals import prepare_candidate_options
from .urban_intelligence import detect_urban_problems, problem_locations_geojson
from .solution_planner import build_solution_plan
from .ai_planning_contract import (
    AI_OUTPUT_SCHEMA,
    AI_SYSTEM_PROMPT,
    build_ai_planning_packet,
    run_ai_planning,
    validate_ai_planning_response,
)


def __getattr__(name: str):
    """Load optional SUMO APIs lazily so their module CLI runs without a duplicate import."""
    if name in {"SumoPreparationError", "load_cached_driving_snapshot", "prepare_sumo_network", "run_real_area_simulation"}:
        module = import_module(".sumo_engine", __name__)
        return getattr(module, name)
    if name in {"get_driving_intervention_catalog", "evaluate_driving_scenario"}:
        module = import_module(".driving_scenarios", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "AreaValidationError",
    "AI_OUTPUT_SCHEMA",
    "AI_SYSTEM_PROMPT",
    "InterventionError",
    "INTERVENTION_CATALOG_VERSION",
    "NeighborhoodCatalogError",
    "OSMData",
    "OSMDataError",
    "StudyArea",
    "SumoPreparationError",
    "acquire_osm_data",
    "analyze_area",
    "analyze_snapshot",
    "build_proposal_context",
    "build_ai_planning_packet",
    "build_solution_plan",
    "evaluate_pedestrian_connection",
    "evaluate_scenario",
    "evaluate_candidates",
    "evaluate_driving_scenario",
    "evaluate_multi_route_impact",
    "discover_intervention_candidates",
    "detect_urban_problems",
    "feature_collection",
    "get_neighborhood",
    "get_neighborhoods",
    "load_neighborhood_catalog",
    "load_cached_driving_snapshot",
    "get_intervention_catalog",
    "get_driving_intervention_catalog",
    "neighborhood_area_input",
    "neighborhoods_geojson",
    "network_metrics",
    "normalize_area",
    "normalize_graph",
    "project_graph",
    "problem_locations_geojson",
    "prepare_candidate_options",
    "prepare_sumo_network",
    "route_between",
    "run_real_area_simulation",
    "run_ai_planning",
    "sample_route_pairs",
    "search_neighborhoods",
    "validate_neighborhood_boundary",
    "validate_proposal",
    "validate_proposal_set",
    "validate_ai_planning_response",
]
