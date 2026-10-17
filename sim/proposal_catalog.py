"""Machine-readable catalog of interventions implemented by the SIM engine."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


INTERVENTION_CATALOG_VERSION = "arteria-sim-interventions-v1"

_CATALOG: dict[str, Any] = {
    "version": INTERVENTION_CATALOG_VERSION,
    "scope": "Deterministic graph evaluation only; no physical feasibility or construction claims.",
    "supported_interventions": [
        {
            "type_id": "add_pedestrian_connection",
            "required_parameters": [
                {"name": "start", "type": "position", "unit": "EPSG:4326", "required": True},
                {"name": "end", "type": "position", "unit": "EPSG:4326", "required": True},
            ],
            "geometric_requirements": [
                "Both endpoints and the straight connecting segment must lie inside the selected study area.",
                "Endpoints must snap to distinct mapped walking-network nodes within the configured limit.",
                "The modeled connection must be longer than zero and no longer than 1000 m.",
            ],
            "allowed_units": ["EPSG:4326", "m", "m/s", "s"],
            "validation_available": True,
            "graph_evaluation_available": True,
            "sumo_evaluation_available": False,
            "required_geographic_evidence": ["validated study-area polygon", "mapped walking graph", "in-area candidate endpoints"],
            "implementation_status": "implemented_graph_only",
        },
        {
            "type_id": "set_connection_enabled",
            "required_parameters": [
                {"name": "connection_id", "type": "stable_modelled_connection_id", "required": True},
                {"name": "enabled", "type": "boolean", "required": True},
            ],
            "geometric_requirements": [
                "The connection ID must identify a modeled ARTERIA connection present in the selected baseline graph.",
            ],
            "allowed_units": [],
            "validation_available": True,
            "graph_evaluation_available": True,
            "sumo_evaluation_available": False,
            "required_geographic_evidence": ["validated study-area polygon", "baseline graph containing the modeled connection"],
            "implementation_status": "implemented_graph_only",
        },
    ],
    "unsupported_examples": [
        {
            "type_id": "traffic_signal_retiming",
            "validation_available": False,
            "graph_evaluation_available": False,
            "sumo_evaluation_available": False,
            "implementation_status": "unsupported",
        },
        {
            "type_id": "new_lane",
            "validation_available": False,
            "graph_evaluation_available": False,
            "sumo_evaluation_available": False,
            "implementation_status": "unsupported",
        },
        {
            "type_id": "underpass",
            "validation_available": False,
            "graph_evaluation_available": False,
            "sumo_evaluation_available": False,
            "implementation_status": "unsupported",
        },
        {
            "type_id": "roundabout",
            "validation_available": False,
            "graph_evaluation_available": False,
            "sumo_evaluation_available": False,
            "implementation_status": "unsupported",
        },
    ],
}


def get_intervention_catalog() -> dict[str, Any]:
    """Return a JSON-ready copy so callers cannot mutate the shared catalog."""
    return deepcopy(_CATALOG)
