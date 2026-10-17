"""Geospatial engine runner with bounded execution and no silent fallback."""
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import BoundedSemaphore

from backend.engine_contract import EngineResult, reject_nonfinite

ROOT = Path(__file__).resolve().parents[1]
_slots = BoundedSemaphore(1)


class SpatialUnavailable(Exception):
    pass


class SpatialTimeout(Exception):
    pass


class SpatialFailure(Exception):
    pass


class SpatialAreaRejected(Exception):
    pass


class SpatialNeighborhoodNotFound(Exception):
    pass


class SpatialAdapter:
    def configuration(self):
        configured = os.getenv("ARTERIA_SIM_ROOT")
        if configured:
            root = Path(configured).resolve()
            revision = os.getenv("ARTERIA_SIM_REVISION", "external-unversioned")
        else:
            root = ROOT
            try:
                revision = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
                ).strip()
                if subprocess.check_output(
                    ["git", "status", "--porcelain", "--", "sim"], cwd=ROOT, text=True,
                    stderr=subprocess.DEVNULL,
                ).strip():
                    revision += "-sim-dirty"
            except (OSError, subprocess.CalledProcessError):
                revision = "in-repository-unversioned"
        if not (root / "sim" / "impact.py").is_file():
            raise SpatialUnavailable("Configured SIM root does not expose graph evaluation")
        return root, revision

    def run(self, request):
        root, revision = self.configuration()
        if not _slots.acquire(blocking=False):
            raise SpatialUnavailable("A graph study is already running; retry when it completes")
        try:
            env = dict(os.environ, ARTERIA_SIM_ROOT=str(root),
                       ARTERIA_SPATIAL_CACHE=str(ROOT / "backend" / ".data" / "osm-cache"))
            completed = subprocess.run([sys.executable, "-m", "backend.spatial_worker"],
                input=request.model_dump_json(), text=True, capture_output=True,
                cwd=ROOT, env=env, timeout=90)
            if completed.returncode:
                try:
                    failure = json.loads(completed.stdout)
                except (json.JSONDecodeError, TypeError):
                    failure = None
                if isinstance(failure, dict) and isinstance(failure.get("error"), dict):
                    detail = failure["error"]
                    if detail.get("code") == "study_area_rejected":
                        raise SpatialAreaRejected(str(detail.get("message", "Selected area is not eligible for standard analysis.")))
                    if detail.get("code") == "unknown_neighborhood":
                        raise SpatialNeighborhoodNotFound("SIM neighborhood catalog ID was not found")
                raise SpatialFailure("Graph engine failed. No substitute results were produced.")
            try:
                result = json.loads(completed.stdout, parse_constant=reject_nonfinite)
                EngineResult.model_validate(result)
            except (ValueError, KeyError, TypeError) as exc:
                raise SpatialFailure("Graph engine returned an incompatible response") from exc
            return result, revision
        except subprocess.TimeoutExpired as exc:
            raise SpatialTimeout("Graph calculation exceeded 90 seconds and was terminated; no fallback was run") from exc
        finally:
            _slots.release()
