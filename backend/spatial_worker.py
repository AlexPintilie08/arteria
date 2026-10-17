"""Subprocess boundary for optional sim code; stdout is only the JSON result."""
import contextlib
import importlib
import json
import os
from pathlib import Path
import sys


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
        data = sim.acquire_osm_data(request["area"], modes=("walk",),
            cache_dir=os.environ["ARTERIA_SPATIAL_CACHE"], max_area_km2=5, max_extent_km=5)
    analysis = sim.analyze_snapshot(data)
    alternatives = sim.evaluate_candidates(data, analysis=analysis,
        sample_count=request["sample_count"], seed=request["seed"],
        max_candidates=request["max_candidates"], max_evaluated_candidates=6,
        candidate_pool_limit=30, route_geometry_limit=16)
    return {"analysis": analysis, "alternatives": alternatives}


if __name__ == "__main__":
    try:
        request = json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):
            result = calculate(request)
        print(json.dumps(result, allow_nan=False))
    except Exception:
        # Traceback is for local server diagnosis; the public API never returns it.
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
