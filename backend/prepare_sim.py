"""Record the SIM revision used directly from this integrated repository."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def prepare(revision=None):
    """Validate the checked-out SIM package and write an ignored provenance manifest.

    The adapter executes the in-repository package directly. An external checkout
    can still be selected explicitly with ARTERIA_SIM_ROOT.
    """
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if revision is not None:
        requested = subprocess.check_output(["git", "rev-parse", "--verify", revision + "^{commit}"], cwd=ROOT, text=True).strip()
        if requested != sha:
            raise ValueError("Only the checked-out integrated SIM revision is supported; set ARTERIA_SIM_ROOT for an external checkout.")
    if not (ROOT / "sim" / "impact.py").is_file():
        raise RuntimeError("Integrated repository does not contain SIM graph evaluation")
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--", "sim"], cwd=ROOT, text=True).strip()
    manifest = {"root": str(ROOT), "revision": sha + ("-sim-dirty" if dirty else "")}
    destination = ROOT / "backend" / ".data" / "sim-engine"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "active.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(prepare(), indent=2))
