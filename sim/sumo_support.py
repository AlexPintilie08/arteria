"""Portable SUMO discovery and an optional, real TraCI simulation smoke test."""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SumoInstallation:
    sumo: Path | None
    netconvert: Path | None
    home: Path | None


def _executable_names(base: str) -> tuple[str, ...]:
    return (f"{base}.exe", base) if os.name == "nt" else (base,)


def _find_under(root: Path, name: str) -> Path | None:
    candidates = [root / name, root / "bin" / name, root / "tools" / name]
    if root.name.casefold() == "bin":
        candidates.insert(0, root / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def discover_sumo(
    environ: dict[str, str] | None = None,
    search_path: str | None = None,
) -> SumoInstallation:
    """Find SUMO through PATH or an explicitly supplied SUMO_HOME directory."""
    env = os.environ if environ is None else environ
    roots: list[Path] = []
    home_value = env.get("SUMO_HOME")
    if home_value:
        roots.append(Path(home_value).expanduser())

    sumo: Path | None = None
    netconvert: Path | None = None
    for root in roots:
        for name in _executable_names("sumo"):
            sumo = _find_under(root, name)
            if sumo:
                break
        for name in _executable_names("netconvert"):
            netconvert = _find_under(root, name)
            if netconvert:
                break

    if sumo is None:
        for name in _executable_names("sumo"):
            found = shutil.which(name, path=search_path)
            if found:
                sumo = Path(found).resolve()
                break
    if netconvert is None:
        for name in _executable_names("netconvert"):
            found = shutil.which(name, path=search_path)
            if found:
                netconvert = Path(found).resolve()
                break

    detected_home = roots[0].resolve() if roots and roots[0].exists() else None
    if detected_home is None and sumo is not None and sumo.parent.name.casefold() == "bin":
        detected_home = sumo.parent.parent
    return SumoInstallation(sumo=sumo, netconvert=netconvert, home=detected_home)


def _python_package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _write_synthetic_scenario(folder: Path) -> tuple[Path, Path]:
    nodes = folder / "nodes.nod.xml"
    edges = folder / "edges.edg.xml"
    network = folder / "network.net.xml"
    routes = folder / "routes.rou.xml"
    nodes.write_text(
        '<nodes><node id="n0" x="0" y="0" type="priority" />'
        '<node id="n1" x="100" y="0" type="priority" /></nodes>',
        encoding="utf-8",
    )
    edges.write_text(
        '<edges><edge id="e0" from="n0" to="n1" priority="1" '
        'numLanes="1" speed="13.9" /></edges>',
        encoding="utf-8",
    )
    routes.write_text(
        '<routes><vType id="car" accel="2.6" decel="4.5" sigma="0" '
        'length="5" maxSpeed="10" /><route id="r0" edges="e0" />'
        '<vehicle id="veh0" type="car" route="r0" depart="0" /></routes>',
        encoding="utf-8",
    )
    return network, routes


def run_sumo_smoke(installation: SumoInstallation) -> str:
    """Build and execute a tiny real SUMO network through the installed TraCI API."""
    if installation.sumo is None:
        raise RuntimeError("SUMO executable was not found on PATH or under SUMO_HOME.")
    if installation.netconvert is None:
        raise RuntimeError("netconvert was not found; the SUMO installation is incomplete.")
    if _python_package_version("traci") is None or _python_package_version("sumolib") is None:
        raise RuntimeError("Python packages traci and sumolib must both be importable.")

    import traci

    with tempfile.TemporaryDirectory(prefix="arteria-sumo-smoke-") as temporary:
        folder = Path(temporary)
        network, routes = _write_synthetic_scenario(folder)
        subprocess.run(
            [
                str(installation.netconvert),
                "--node-files",
                str(folder / "nodes.nod.xml"),
                "--edge-files",
                str(folder / "edges.edg.xml"),
                "--output-file",
                str(network),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

        traci.start(
            [
                str(installation.sumo),
                "--net-file",
                str(network),
                "--route-files",
                str(routes),
                "--end",
                "30",
                "--no-step-log",
                "true",
            ],
            stdout=subprocess.DEVNULL,
        )
        try:
            traci.simulationStep()
            time_seconds = float(traci.simulation.getTime())
            if time_seconds <= 0:
                raise RuntimeError("SUMO did not advance the synthetic scenario.")
        finally:
            traci.close()

    version = subprocess.run(
        [str(installation.sumo), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.splitlines()[0]
    return f"{version}; TraCI advanced the synthetic scenario to {time_seconds:g}s"


def report_status(run_smoke: bool = False) -> int:
    installation = discover_sumo()
    traci_version = _python_package_version("traci")
    sumolib_version = _python_package_version("sumolib")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"SUMO executable: {installation.sumo or 'not found'}")
    print(f"netconvert: {installation.netconvert or 'not found'}")
    configured_home = os.environ.get("SUMO_HOME")
    print(f"SUMO_HOME: {configured_home or 'not set (discovery uses PATH)'}")
    if installation.home and not configured_home:
        print(f"Detected installation root: {installation.home}")
    print(f"Python traci: {traci_version or 'not installed'}")
    print(f"Python sumolib: {sumolib_version or 'not installed'}")

    if not run_smoke:
        if installation.sumo and installation.netconvert and traci_version and sumolib_version:
            print("Optional SUMO: detected; run with --smoke to verify an actual simulation.")
        else:
            print("Optional SUMO: not ready; frontend/backend startup does not require it.")
        return 0

    if installation.sumo is None:
        print("Optional SUMO smoke: skipped; no SUMO executable was found.")
        if sys.platform == "darwin":
            print("Fallback: the pinned binary supports macOS 15+ ARM64; use the official SUMO macOS package on other configurations.")
        elif os.name == "nt":
            print("Fallback: use the official SUMO Windows installer or portable ZIP.")
        return 0

    try:
        result = run_sumo_smoke(installation)
    except Exception as error:  # noqa: BLE001 - surface optional native-toolchain failures clearly
        print(f"Optional SUMO smoke: FAILED ({error})")
        return 1
    print(f"Optional SUMO smoke: PASSED ({result})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run a real temporary network and one TraCI simulation step when SUMO is available",
    )
    args = parser.parse_args()
    return report_status(run_smoke=args.smoke)


if __name__ == "__main__":
    raise SystemExit(main())
