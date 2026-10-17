"""Export a local Git revision to an ignored snapshot without merging or editing sim/."""
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def prepare(revision="origin/feat/sim-engine"):
    sha = subprocess.check_output(["git", "rev-parse", "--verify", revision + "^{commit}"], cwd=ROOT, text=True).strip()
    destination = ROOT / "backend" / ".data" / "sim-engine" / sha
    if not (destination / "sim" / "impact.py").exists():
        archive = subprocess.check_output(["git", "archive", sha, "sim"], cwd=ROOT)
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(destination, filter="data")
    if not (destination / "sim" / "impact.py").exists():
        raise RuntimeError("Selected revision does not contain the graph evaluation API")
    manifest = {"root": str(destination), "revision": sha}
    (destination.parent / "active.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(prepare(), indent=2))
