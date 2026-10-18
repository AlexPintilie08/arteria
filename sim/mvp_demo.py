"""Create a reproducible, offline-first SIM report and GeoJSON evidence package."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analysis import analyze_snapshot
from .demo import fixture_snapshot, load_cached_snapshot
from .driving_scenarios import evaluate_driving_scenario, get_driving_intervention_catalog
from .geo import LAYER_TAGS, OSMData, acquire_osm_data, normalize_area
from .impact import evaluate_candidates
from .proposal_context import build_proposal_context
from .proposal_validation import validate_proposal_set
from .proposals import prepare_candidate_options
from .sumo_engine import load_cached_driving_snapshot, run_real_area_simulation


def _read_area(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read the explicit area JSON {path}: {error}") from error


def _candidate_geojson(evaluation: dict[str, Any], analysis: dict[str, Any], data: OSMData) -> dict[str, Any]:
    features: list[dict[str, Any]] = []
    for issue in analysis.get("issue_geojson", {}).get("features", []):
        features.append({
            **issue,
            "properties": {**issue.get("properties", {}), "layer": "analysis_issue"},
        })
    for candidate in evaluation.get("ranked_candidates", []):
        if candidate.get("geometry"):
            features.append({
                "type": "Feature",
                "id": candidate.get("candidate_id"),
                "geometry": candidate["geometry"],
                "properties": {
                    "layer": "conditional_pedestrian_candidate",
                    "candidate_id": candidate.get("candidate_id"),
                    "shared_sample_outcome_status": candidate.get("shared_sample_outcome_status"),
                    "impact_evidence_status": candidate.get("impact_evidence_status"),
                    "geographic_evidence_status": candidate.get("geographic_evidence_status"),
                    "physical_feasibility": candidate.get("screening", {}).get("physical_feasibility", "unknown"),
                },
            })
        for endpoint in ("start", "end"):
            endpoint_data = candidate.get(endpoint, {})
            coordinates = endpoint_data.get("coordinates") if isinstance(endpoint_data, dict) else None
            if isinstance(coordinates, (list, tuple)) and len(coordinates) == 2:
                features.append({
                    "type": "Feature",
                    "id": f"{candidate.get('candidate_id')}:{endpoint}",
                    "geometry": {"type": "Point", "coordinates": list(coordinates)},
                    "properties": {"layer": "candidate_endpoint", "candidate_id": candidate.get("candidate_id"), "endpoint": endpoint, "graph_node_id": endpoint_data.get("node_id")},
                })
        for evidence_kind in ("shared_sample_impact", "targeted_diagnostic_impact"):
            impact = candidate.get("impact") if evidence_kind == "shared_sample_impact" else candidate.get("targeted_diagnostic_impact")
            if not isinstance(impact, dict):
                continue
            sample_kind = "shared_sample" if evidence_kind == "shared_sample_impact" else "targeted_diagnostic_only"
            for route in impact.get("routes", []):
                for phase in ("before", "after"):
                    geometry = route.get(phase, {}).get("geometry") if isinstance(route.get(phase), dict) else None
                    if geometry:
                        features.append({
                            "type": "Feature",
                            "id": f"{candidate.get('candidate_id')}:{sample_kind}:{route.get('origin_node_id')}:{route.get('destination_node_id')}:{phase}",
                            "geometry": geometry,
                            "properties": {
                                "layer": "calculated_graph_route",
                                "evidence_sample": sample_kind,
                                "candidate_id": candidate.get("candidate_id"),
                                "origin_node_id": route.get("origin_node_id"),
                                "destination_node_id": route.get("destination_node_id"),
                                "phase": phase,
                                "status": route.get(phase, {}).get("status"),
                            },
                        })
    for candidate in evaluation.get("rejected_candidates", []):
        if candidate.get("geometry"):
            features.append({
                "type": "Feature", "id": candidate.get("candidate_id"), "geometry": candidate["geometry"],
                "properties": {"layer": "screened_out_candidate", "candidate_id": candidate.get("candidate_id"), "screening": candidate.get("screening", {})},
            })
    source = data.metadata.get("source")
    return {
        "type": "FeatureCollection",
        "metadata": {
            "source": source,
            "retrieved_at": data.metadata.get("retrieved_at"),
            "study_area": {"city_id": data.area.city_id, "area_id": data.area.area_id, "boundary_source": data.area.boundary_source},
            "crs": "EPSG:4326",
            "attribution": "© OpenStreetMap contributors" if source == "OpenStreetMap" else "Synthetic fixture; no OSM source data.",
            "attribution_url": "https://www.openstreetmap.org/copyright" if source == "OpenStreetMap" else None,
            "license": "ODbL-1.0" if source == "OpenStreetMap" else None,
            "limitations": ["Route geometries are calculated graph routes, not observed GPS traces.", "Candidate lines are conditional and feasibility is unknown."],
        },
        "features": features,
    }


def _markdown_report(result: dict[str, Any]) -> str:
    analysis = result["analysis"]
    validation = result["proposal_validation"]
    source = result["study"]["source"]
    lines = [
        "# ARTERIA SIM MVP report",
        "",
        f"- Source mode: `{source['mode']}`",
        f"- Data source: `{source.get('source_name') or 'unknown'}`",
        f"- Study area: `{result['study']['area_id']}` ({result['study'].get('city_id') or 'unknown city'})",
        f"- Source area equivalence: `{source.get('area_equivalence', 'not_applicable')}`",
        f"- Retrieved at: `{source.get('retrieved_at') or 'unknown'}`",
        f"- Network requests made: `{str(source.get('network_requests_made', False)).lower()}`",
        "",
        "## Analysis and evidence",
        "",
        f"- Available networks: `{', '.join(sorted(analysis.get('network_metrics', {}))) or 'none'}`",
        f"- Candidate status: `{result['candidate_evaluation'].get('recommendation_status')}`",
        f"- Evaluated candidates: `{len(result['candidate_evaluation'].get('ranked_candidates', []))}`",
        f"- Proposal validation: `{validation.get('summary', {})}`",
        f"- Candidate GeoJSON features: `{result['geojson_feature_count']}` (calculated graph routes are not GPS observations)",
        "",
        "## Optional SUMO",
        "",
        f"- Baseline: `{(result.get('sumo_baseline') or {}).get('status', 'not_requested')}`",
        f"- Paired scenario: `{(result.get('sumo_comparison') or {}).get('status', 'not_requested')}`",
        "- SUMO demand is synthetic. Simulator outputs are not measured urban traffic or calibrated forecasts.",
        "",
        "## Limitations",
        "",
    ]
    lines.extend(f"- {item}" for item in result["limitations"])
    lines.append("")
    return "\n".join(lines)


def run_mvp_demo(
    *,
    source: str,
    output_dir: str | Path,
    cache_dir: str | Path | None = None,
    area_json: str | Path | None = None,
    acquire: bool = False,
    feature_categories: tuple[str, ...] = ("buildings", "schools", "healthcare", "services"),
    sumo_baseline: bool = False,
    paired_sumo_edge_id: str | None = None,
    paired_speed_mps: float = 5.0,
) -> dict[str, Any]:
    """Run only the selected source mode; no cache miss silently downloads or falls back."""
    if source not in {"fixture", "cache", "area"}:
        raise ValueError("source must be one of: fixture, cache, area.")
    if source == "cache":
        if cache_dir is None:
            raise ValueError("source='cache' requires an explicit --cache-dir.")
        data = load_cached_snapshot(cache_dir)
        source_mode = {"mode": "cache", "source_name": data.metadata.get("source"), "retrieved_at": data.metadata.get("retrieved_at"), "network_requests_made": False, "area_equivalence": data.metadata.get("cache", {}).get("area_equivalence_verified", False)}
        if "drive" not in data.graphs:
            try:
                drive_data = load_cached_driving_snapshot(cache_dir)
            except FileNotFoundError:
                drive_data = None
            walk_source_area = data.metadata.get("source_area", {})
            drive_source_area = drive_data.metadata.get("source_area", {}) if drive_data is not None else {}
            same_verified_geometry = (
                isinstance(walk_source_area, dict)
                and isinstance(drive_source_area, dict)
                and walk_source_area.get("source_geometry_sha256")
                and walk_source_area.get("source_geometry_sha256") == drive_source_area.get("source_geometry_sha256")
            )
            if drive_data is not None and drive_data.area.area_id == data.area.area_id and same_verified_geometry:
                data.graphs["drive"] = drive_data.graphs["drive"]
                data.metadata["driving_graph_join_status"] = "same_verified_source_geometry"
            elif drive_data is not None:
                data.metadata["driving_graph_join_status"] = "not_joined_source_geometry_unverified_or_mismatched"
    elif source == "area":
        if area_json is None:
            raise ValueError("source='area' requires --area-json containing a bounded Polygon/MultiPolygon or bbox descriptor.")
        area = _read_area(Path(area_json))
        if not acquire:
            normalized_area = normalize_area(area)
            empty = fixture_snapshot()
            data = OSMData(
                area=normalized_area,
                graphs={},
                layers=empty.layers,
                layer_availability={name: {"status": "unknown", "feature_count": None} for name in LAYER_TAGS},
                metadata={"source": "not acquired", "source_version": None, "retrieved_at": None, "working_crs": normalized_area.working_crs, "limitations": ["The selected area was validated, but no OSM acquisition was requested."]},
                warnings=["No source dataset was acquired; all geography and network measures remain unavailable."],
            )
            source_mode = {"mode": "area", "source_name": "not acquired", "retrieved_at": None, "network_requests_made": False, "area_equivalence": "not_acquired"}
        else:
            data = acquire_osm_data(area, modes=("walk", "drive"), feature_categories=feature_categories)
            source_mode = {"mode": "area", "source_name": data.metadata.get("source"), "retrieved_at": data.metadata.get("retrieved_at"), "network_requests_made": True, "area_equivalence": "verified_by_requested_geometry"}
    else:
        if acquire or area_json is not None:
            raise ValueError("fixture mode is deterministic and does not accept --acquire or --area-json.")
        data = fixture_snapshot()
        source_mode = {"mode": "fixture", "source_name": data.metadata.get("source"), "retrieved_at": None, "network_requests_made": False, "area_equivalence": "synthetic_fixture"}

    analysis = analyze_snapshot(data)
    evaluation = evaluate_candidates(data, analysis=analysis)
    context = build_proposal_context(data, analysis, evaluation)
    options = prepare_candidate_options(analysis, evaluation)
    validation = validate_proposal_set(options, data=data, candidate_evaluation=evaluation)
    geojson = _candidate_geojson(evaluation, analysis, data)
    baseline_result = None
    paired_result = None
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty demo output directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    if sumo_baseline:
        if "drive" not in data.graphs:
            baseline_result = {"status": "unavailable", "reason": "The selected source snapshot has no driving graph; no OSM fallback was attempted."}
        else:
            baseline_result = run_real_area_simulation(data, output / "sumo-baseline", vehicle_count=20, seed=4092, duration_seconds=180, execution_timeout_seconds=60)
    if paired_sumo_edge_id:
        catalog = get_driving_intervention_catalog(data)
        target = next((item for item in catalog.get("targets", []) if item.get("sumo_edge_id") == paired_sumo_edge_id), None)
        if target is None:
            paired_result = {"schema_version": "arteria.sumo-comparison.v1", "status": "unavailable", "reason": "The requested edge ID is not present in the selected source's current versioned driving intervention catalog."}
        else:
            intervention = {
                "schema_version": "arteria.driving-intervention.v1",
                "action": "set_drive_edge_speed_limit",
                "target": {key: target[key] for key in ("sumo_edge_id", "network_revision", "source_osm_way_ids")},
                "parameters": {"speed_limit_mps": paired_speed_mps},
            }
            paired_result = evaluate_driving_scenario(data, intervention, output / "sumo-paired", vehicle_count=20, seed=4092, duration_seconds=180, execution_timeout_seconds=60)

    result = {
        "schema_version": "arteria.mvp-demo.v1",
        "study": {"city_id": data.area.city_id, "area_id": data.area.area_id, "boundary_source": data.area.boundary_source, "geometry_wgs84": data.area.geojson, "extent_wgs84": data.area.extent, "working_crs": data.area.working_crs, "source": source_mode},
        "analysis": analysis,
        "candidate_evaluation": evaluation,
        "evidence_packet": context,
        "candidate_options": options,
        "proposal_validation": validation,
        "geojson_feature_count": len(geojson["features"]),
        "sumo_baseline": baseline_result,
        "sumo_comparison": paired_result,
        "limitations": [
            "OSM tags and road/pedestrian graph coverage are incomplete; absent mapped features are not proof of real-world absence.",
            "Graph-node route pairs and route geometries are calculated analysis probes, not observed journeys or population demand.",
            "Candidate geometry is conditional; legal, safety, ownership and construction feasibility remain unknown.",
            "Cloud LLM inference is not called by this demo; proposal validation checks supplied options against SIM evidence only.",
            "SUMO demand is synthetic and SUMO metrics are simulated outputs, not real measured urban traffic.",
        ],
    }
    (output / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    (output / "candidate-evidence.geojson").write_text(json.dumps(geojson, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    (output / "summary.md").write_text(_markdown_report(result), encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("fixture", "cache", "area"), default="fixture")
    parser.add_argument("--cache-dir", help="required explicit path when --source cache is selected")
    parser.add_argument("--area-json", help="file containing the explicit bounded area input when --source area is selected")
    parser.add_argument("--acquire", action="store_true", help="explicitly permit OSM acquisition for --source area")
    parser.add_argument("--feature-categories", default="buildings,schools,healthcare,services", help="comma-separated supported OSM category IDs for explicit area acquisition")
    parser.add_argument("--sumo-baseline", action="store_true", help="request optional bounded SUMO baseline execution when a drive graph is present")
    parser.add_argument("--paired-sumo-edge-id", help="exact current edge ID from get_driving_intervention_catalog(data)")
    parser.add_argument("--paired-speed-mps", type=float, default=5.0)
    parser.add_argument("--output-dir", help="ignored local output directory; defaults to sim/.cache/mvp-demo/<UTC timestamp>")
    args = parser.parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent / ".cache" / "mvp-demo" / timestamp
    categories = tuple(value.strip() for value in args.feature_categories.split(",") if value.strip())
    result = run_mvp_demo(
        source=args.source, output_dir=output, cache_dir=args.cache_dir, area_json=args.area_json,
        acquire=args.acquire, feature_categories=categories, sumo_baseline=args.sumo_baseline,
        paired_sumo_edge_id=args.paired_sumo_edge_id, paired_speed_mps=args.paired_speed_mps,
    )
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"SIM MVP demo status: {result['proposal_validation'].get('summary', {})}")
    print(f"Report JSON: {output / 'report.json'}")
    print(f"Candidate GeoJSON: {output / 'candidate-evidence.geojson'}")
    print(f"Summary Markdown: {output / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
