"""Subprocess boundary for optional sim code; stdout is only the JSON result."""
import contextlib
import importlib
import json
import os
from pathlib import Path
import sys


class WorkerRequestError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def calculate(request):
    root = Path(os.environ["ARTERIA_SIM_ROOT"]).resolve()
    sys.path.insert(0, str(root))
    sim = importlib.import_module("sim")
    if not Path(sim.__file__).resolve().is_relative_to(root):
        raise RuntimeError("Engine was not loaded from the configured snapshot")
    if request["source"] == "fixture":
        fixture = importlib.import_module("sim.demo")
        data = fixture.fixture_snapshot()
    else:
        neighborhood = sim.get_neighborhood(request["neighborhood_id"])
        if neighborhood is None:
            raise WorkerRequestError("unknown_neighborhood", "SIM neighborhood catalog ID was not found.")
        validation = sim.validate_neighborhood_boundary(neighborhood)
        if validation.get("status") == "point_only":
            raise WorkerRequestError("study_area_rejected", "This OSM record is a point only; SIM does not infer a study boundary.")
        if not validation.get("analysis_eligible"):
            raise WorkerRequestError("study_area_rejected", str(validation.get("reason") or "Selected OSM area is not eligible for standard analysis."))
        try:
            area = sim.neighborhood_area_input(neighborhood)
        except sim.AreaValidationError as exc:
            raise WorkerRequestError("study_area_rejected", str(exc)) from exc
        data = sim.acquire_osm_data(area, modes=("walk",),
            cache_dir=os.environ["ARTERIA_SPATIAL_CACHE"], max_area_km2=5, max_extent_km=5,
            include_features=True,
            feature_categories=("schools", "healthcare", "public_transport", "crossings"))
    analysis = sim.analyze_snapshot(data)
    alternatives = sim.evaluate_candidates(data, analysis=analysis,
        sample_count=request["sample_count"], seed=request["seed"],
        max_candidates=request["max_candidates"], max_evaluated_candidates=6,
        candidate_pool_limit=30, route_geometry_limit=16)
    options = sim.prepare_candidate_options(analysis, alternatives)
    validation = sim.validate_proposal_set(options, data=data, candidate_evaluation=alternatives)
    evidence_packet = sim.build_proposal_context(data, analysis, alternatives)
    urban_issues = sim.detect_urban_problems(
        data, analysis=analysis, candidate_evaluation=alternatives)
    solution_plan = sim.build_solution_plan(data, analysis, urban_issues, alternatives)
    ai_evidence_packet = sim.build_ai_planning_packet(
        data, analysis, urban_issues, alternatives, solution_plan)
    problem_locations = sim.problem_locations_geojson(urban_issues)
    return {"analysis": analysis, "alternatives": alternatives, "proposal_options": options,
            "proposal_validation": validation, "evidence_packet": evidence_packet,
            "urban_issues": urban_issues, "solution_plan": solution_plan,
            "ai_evidence_packet": ai_evidence_packet,
            "problem_locations_geojson": problem_locations}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            result = calculate(request)
        print(json.dumps(result, allow_nan=False))
    except WorkerRequestError as exc:
        print(json.dumps({"error": {"code": exc.code, "message": str(exc)}}, allow_nan=False))
        sys.exit(2)
    except Exception:
        # Traceback is for local server diagnosis; the public API never returns it.
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
