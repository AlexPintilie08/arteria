"""Create a reproducible, offline-first SIM report and GeoJSON evidence package."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .analysis import analyze_snapshot
from .demo import fixture_snapshot, load_cached_snapshot
from .driving_scenarios import evaluate_driving_scenario, get_driving_intervention_catalog
from .geo import LAYER_TAGS, OSMData, acquire_osm_data, normalize_area
from .impact import evaluate_candidates
from .proposal_context import build_proposal_context
from .proposal_validation import validate_proposal_set
from .proposals import prepare_candidate_options
from .sumo_engine import load_cached_driving_snapshot, run_real_area_simulation
from .urban_intelligence import detect_urban_problems, problem_locations_geojson
from .solution_planner import build_solution_plan
from .ai_planning_contract import AI_OUTPUT_SCHEMA, AI_SYSTEM_PROMPT, build_ai_planning_packet, run_ai_planning


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
    if isinstance(result.get("urban_issues"), dict):
        urban = result["urban_issues"]
        plan = result.get("solution_plan", {})
        mock = result.get("mock_ai", {})
        lines.extend([
            "",
            "## Urban planning preview",
            "",
            f"- Detected evidence-backed problems: `{len(urban.get('problems', []))}`",
            f"- Problem types: `{', '.join(sorted({str(item.get('problem_type')) for item in urban.get('problems', []) if isinstance(item, dict)})) or 'none'}`",
            f"- Candidate-backed options: `{sum(item.get('status') in {'supported_evaluated', 'supported_not_yet_evaluated'} for item in plan.get('solutions', []) if isinstance(item, dict))}`",
            f"- Conceptual options: `{sum(item.get('status') == 'concept_only_not_evaluated' for item in plan.get('solutions', []) if isinstance(item, dict))}`",
            f"- AI contract example: `{mock.get('status', 'not_run')}` (`{mock.get('provider', 'none')}`; no live cloud inference)",
            f"- AI evidence packet: `{result.get('ai_packet_bytes', 0)}` bytes",
        ])
    lines.append("")
    return "\n".join(lines)


def _mock_ai_response(packet: dict[str, Any]) -> dict[str, Any]:
    urban = packet["urban_intelligence"]
    plan = packet["solution_plan"]
    problems = urban.get("problems", [])
    available_solutions = plan.get("solutions", [])
    selected_solutions = available_solutions[:8]
    available_problem_ids = {
        item.get("problem_id") for item in problems if isinstance(item, dict)
    }
    available_evidence_ids = {
        evidence.get("evidence_id")
        for problem in problems if isinstance(problem, dict)
        for evidence in (problem.get("evidence", []) if isinstance(problem.get("evidence"), list) else [])
        if isinstance(evidence, dict) and isinstance(evidence.get("evidence_id"), str)
    }
    available_evidence_ids.update(
        item.get("gap_id") for item in urban.get("coverage_gaps", [])
        if isinstance(item, dict) and isinstance(item.get("gap_id"), str)
    )
    available_evidence_ids.update(
        item.get("observation_id") for item in urban.get("simulation_observations", [])
        if isinstance(item, dict) and isinstance(item.get("observation_id"), str)
    )
    identified = []
    for problem in problems[:12]:
        evidence = problem.get("evidence", [])
        evidence_ids = [item["evidence_id"] for item in evidence if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)]
        if evidence_ids:
            identified.append({
                "problem_id": problem["problem_id"],
                "explanation": "Dovezile SIM indică o posibilă problemă în rețeaua mapată; verificarea în teren rămâne necesară.",
                "evidence_ids": evidence_ids[:8],
            })
    recommendations = []
    candidate_ids = []
    refs = {evidence_id for item in identified for evidence_id in item["evidence_ids"]}
    for solution in selected_solutions:
        evidence_ids = [value for value in solution.get("evidence_ids", []) if isinstance(value, str)]
        problem_ids = solution.get("problem_ids", [])
        if (
            not evidence_ids
            or not all(isinstance(value, str) for value in evidence_ids)
            or not set(evidence_ids).issubset(available_evidence_ids)
            or not isinstance(problem_ids, list)
            or not all(isinstance(value, str) for value in problem_ids)
            or not set(problem_ids).issubset(available_problem_ids)
        ):
            continue
        refs.update(evidence_ids)
        candidate_id = solution.get("candidate_id")
        if candidate_id:
            candidate_ids.append(candidate_id)
        recommendations.append({
            "solution_id": solution["solution_id"],
            "candidate_id": candidate_id,
            "problem_ids": solution.get("problem_ids", []),
            "title": solution["title"],
            "explanation": "Opțiunea este legată de dovezile citate; geometria și orice impact calculat sunt atașate din rezultatul autoritativ SIM.",
            "expected_benefit_type": solution["expected_benefit_type"],
            "evidence_ids": evidence_ids[:8],
            "field_verification_required": True,
        })
    return {
        "schema_version": "arteria.ai-planning-response.v1",
        "area_id": packet["study_area"]["area_id"],
        "evidence_packet_sha256": packet["integrity"]["sha256"],
        "summary": "Previzualizare deterministă a contractului AI, construită numai din dovezile SIM furnizate.",
        "identified_problems": identified,
        "recommended_solutions": recommendations,
        "supported_candidate_ids": sorted(set(candidate_ids)),
        "evidence_references": sorted(refs),
        "limitations": ["Eșantionul de rețea este calculat, iar datele mapate pot fi incomplete."],
        "requires_field_verification": True,
    }


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
    planning: bool = False,
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
            cache_metadata = data.metadata.get("cache", {})
            requested_modes = data.metadata.get("requested_network_modes", [])
            cached_modes = cache_metadata.get("cached_network_modes", []) if isinstance(cache_metadata, Mapping) else []
            feature_query_requested = data.metadata.get("feature_query_requested", True)
            features_cached = cache_metadata.get("features_cache_hit", False) if isinstance(cache_metadata, Mapping) else False
            all_requested_data_cached = (
                isinstance(requested_modes, list)
                and bool(requested_modes)
                and set(requested_modes).issubset(cached_modes if isinstance(cached_modes, list) else [])
                and (not feature_query_requested or features_cached)
            )
            source_mode = {
                "mode": "area",
                "source_name": data.metadata.get("source"),
                "retrieved_at": data.metadata.get("retrieved_at"),
                "network_requests_made": not all_requested_data_cached,
                "area_equivalence": "verified_by_requested_geometry",
            }
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
    if planning:
        urban_issues = detect_urban_problems(data, analysis=analysis, candidate_evaluation=evaluation)
        solution_plan = build_solution_plan(data, analysis, urban_issues, evaluation)
        ai_packet = build_ai_planning_packet(data, analysis, urban_issues, evaluation, solution_plan)
        mock_ai = run_ai_planning(ai_packet, lambda **_: _mock_ai_response(ai_packet))
        result.update({
            "urban_issues": urban_issues,
            "solution_plan": solution_plan,
            "ai_packet_bytes": ai_packet["integrity"]["serialized_bytes"],
            "ai_packet_sha256": ai_packet["integrity"]["sha256"],
            "mock_ai": {"provider": "deterministic_mock", "live_cloud_inference": False, **mock_ai},
        })
        (output / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        (output / "urban_problems.json").write_text(json.dumps(urban_issues, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        (output / "solutions.json").write_text(json.dumps(solution_plan, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        (output / "ai_evidence_packet.json").write_text(json.dumps(ai_packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False), encoding="utf-8", newline="\n")
        (output / "ai_input_example.json").write_text(json.dumps({"system_prompt": AI_SYSTEM_PROMPT, "output_schema": AI_OUTPUT_SCHEMA, "evidence_packet": ai_packet}, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        (output / "ai_output_schema.json").write_text(json.dumps(AI_OUTPUT_SCHEMA, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        (output / "candidate_evidence.geojson").write_text(json.dumps(geojson, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        (output / "problem_locations.geojson").write_text(json.dumps(problem_locations_geojson(urban_issues), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
        (output / "validation_report.json").write_text(json.dumps({
            "schema_version": "arteria.mvp-planning-validation-report.v1",
            "candidate_validation": solution_plan["candidate_validation"],
            "ai_provider": "deterministic_mock",
            "live_cloud_inference": False,
            "ai_run": result["mock_ai"],
            "ai_response_validation": result["mock_ai"].get("validation"),
        }, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
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
    parser.add_argument("--planning", action="store_true", help="write bounded urban issue, solution, and mock AI contract artifacts")
    parser.add_argument("--output-dir", help="ignored local output directory; defaults to sim/.cache/mvp-demo/<UTC timestamp>")
    args = parser.parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent / ".cache" / "mvp-demo" / timestamp
    categories = tuple(value.strip() for value in args.feature_categories.split(",") if value.strip())
    result = run_mvp_demo(
        source=args.source, output_dir=output, cache_dir=args.cache_dir, area_json=args.area_json,
        acquire=args.acquire, feature_categories=categories, sumo_baseline=args.sumo_baseline,
        paired_sumo_edge_id=args.paired_sumo_edge_id, paired_speed_mps=args.paired_speed_mps, planning=args.planning,
    )
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"SIM MVP demo status: {result['proposal_validation'].get('summary', {})}")
    print(f"Report JSON: {output / 'report.json'}")
    print(f"Candidate GeoJSON: {output / 'candidate-evidence.geojson'}")
    print(f"Summary Markdown: {output / 'summary.md'}")
    if args.planning:
        print(f"Urban problems: {output / 'urban_problems.json'}")
        print(f"Solutions: {output / 'solutions.json'}")
        print(f"AI evidence packet: {output / 'ai_evidence_packet.json'} ({result['ai_packet_bytes']} bytes)")
        print(f"Problem GeoJSON: {output / 'problem_locations.geojson'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
