"""Copy the canonical SIM catalog and export its default boundary checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sim-workspace", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()

    sim_workspace = args.sim_workspace.resolve()
    source = sim_workspace / "sim" / "iasi-neighborhoods.geojson"
    if not source.is_file():
        parser.error(f"SIM catalog not found: {source}")

    sys.path.insert(0, str(sim_workspace))
    from sim.neighborhoods import load_neighborhood_catalog, validate_neighborhood_boundary

    records = load_neighborhood_catalog(source)
    checks = [validate_neighborhood_boundary(record, source) for record in records]
    source_bytes = source.read_bytes()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    catalog_target = args.output_directory / "iasi-neighborhoods.geojson"
    catalog_target.write_bytes(source_bytes)

    validation = {
        "source_catalog": "sim/iasi-neighborhoods.geojson",
        "catalog_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "coordinate_reference_system": "EPSG:4326",
        "default_limits": {"max_area_km2": 5.0, "max_extent_km": 5.0},
        "records": {check["id"]: check for check in checks},
    }
    validation_target = args.output_directory / "iasi-neighborhood-validation.json"
    validation_target.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"Exported {len(records)} records ({sum(record['geometry_type'] in {'Polygon', 'MultiPolygon'} for record in records)} polygons, "
        f"{sum(record['geometry_type'] == 'Point' for record in records)} points) to {args.output_directory}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
