"""Offline tests for urban intelligence, solution planning, and the AI contract."""

from __future__ import annotations

import copy
import json
import math
import time
from pathlib import Path

import geopandas as gpd
import networkx as nx
import pytest
from pyproj import Transformer
from shapely.geometry import LineString, Point

from sim import (
    AI_OUTPUT_SCHEMA,
    AI_SYSTEM_PROMPT,
    acquire_osm_data,
    analyze_snapshot,
    build_ai_planning_packet,
    build_solution_plan,
    detect_urban_problems,
    evaluate_candidates,
    problem_locations_geojson,
    run_ai_planning,
    validate_ai_planning_response,
)
from sim.ai_planning_contract import AI_RESPONSE_SCHEMA, MAX_AI_PACKET_BYTES
from sim.demo import fixture_snapshot
from sim.mvp_demo import run_mvp_demo


@pytest.fixture(scope="module")
def planning_case() -> dict:
    data = fixture_snapshot()
    analysis = analyze_snapshot(data)
    evaluation = evaluate_candidates(data, analysis=analysis, sample_count=8, seed="urban-test-v1")
    issues = detect_urban_problems(data, analysis=analysis, candidate_evaluation=evaluation, route_pair_sample_count=32)
    plan = build_solution_plan(data, analysis, issues, evaluation)
    packet = build_ai_planning_packet(data, analysis, issues, evaluation, plan)
    return {"data": data, "analysis": analysis, "evaluation": evaluation, "issues": issues, "plan": plan, "packet": packet}


def _valid_response(case: dict) -> dict:
    packet = case["packet"]
    problems = packet["urban_intelligence"]["problems"]
    plan = packet["solution_plan"]["solutions"]
    identified = []
    refs: set[str] = set()
    for problem in problems[:3]:
        evidence_ids = [record["evidence_id"] for record in problem["evidence"] if record.get("evidence_id")]
        if not evidence_ids:
            continue
        refs.update(evidence_ids)
        identified.append({
            "problem_id": problem["problem_id"],
            "explanation": "Dovezile SIM indică o posibilă problemă în rețeaua mapată; verificarea în teren rămâne necesară.",
            "evidence_ids": evidence_ids,
        })
    selected = next(item for item in plan if item.get("evidence_ids"))
    refs.update(selected["evidence_ids"])
    return {
        "schema_version": AI_RESPONSE_SCHEMA,
        "area_id": packet["study_area"]["area_id"],
        "evidence_packet_sha256": packet["integrity"]["sha256"],
        "summary": "Dovezile mapate susțin verificarea problemelor și soluțiilor citate.",
        "identified_problems": identified,
        "recommended_solutions": [{
            "solution_id": selected["solution_id"],
            "candidate_id": selected.get("candidate_id"),
            "problem_ids": selected.get("problem_ids", []),
            "title": selected["title"],
            "explanation": "Opțiunea este legată de problema citată și necesită verificarea în teren.",
            "expected_benefit_type": selected["expected_benefit_type"],
            "evidence_ids": selected["evidence_ids"],
            "field_verification_required": True,
        }],
        "supported_candidate_ids": [selected["candidate_id"]] if selected.get("candidate_id") else [],
        "evidence_references": sorted(refs),
        "limitations": ["Datele mapate pot fi incomplete; rezultatele descriu numai dovezile SIM furnizate."],
        "requires_field_verification": True,
    }


def _set_wgs84(graph: nx.Graph, area, node: object, coordinate: tuple[float, float]) -> None:
    transformer = Transformer.from_crs("EPSG:4326", area.working_crs, always_xy=True)
    graph.nodes[node]["x"], graph.nodes[node]["y"] = transformer.transform(*coordinate)


def test_disconnections_are_stable_bounded_and_exported_as_valid_wgs84(planning_case: dict) -> None:
    data = planning_case["data"]
    first = detect_urban_problems(data, analysis=planning_case["analysis"], candidate_evaluation=planning_case["evaluation"], route_pair_sample_count=32)
    second = detect_urban_problems(data, analysis=planning_case["analysis"], candidate_evaluation=planning_case["evaluation"], route_pair_sample_count=32)
    assert first["schema_version"] == "arteria.urban-issues.v1"
    assert len(first["problems"]) <= 12
    assert any(problem["problem_type"] == "pedestrian_disconnection" for problem in first["problems"])
    assert [item["problem_id"] for item in first["problems"]] == [item["problem_id"] for item in second["problems"]]
    assert all(item["data_confidence"] == "synthetic" for item in first["problems"])
    geojson = problem_locations_geojson(first)
    for feature in geojson["features"]:
        assert feature["geometry"]["type"] in {"Point", "LineString"}
        coordinates = feature["geometry"]["coordinates"]
        points = [coordinates] if feature["geometry"]["type"] == "Point" else coordinates
        assert all(-180 <= point[0] <= 180 and -90 <= point[1] <= 90 for point in points)
    json.dumps(first, ensure_ascii=False, allow_nan=False)


def test_clipped_component_is_localized_as_uncertain(planning_case: dict) -> None:
    data = fixture_snapshot()
    data.graphs["walk"].add_node(8)
    _set_wgs84(data.graphs["walk"], data.area, 8, (27.5756, 47.163))
    analysis = analyze_snapshot(data)
    issues = detect_urban_problems(data, analysis=analysis, route_pair_sample_count=16)
    assert any(
        problem["problem_type"] == "pedestrian_disconnection"
        and problem["severity"] == "unknown"
        and problem["evidence"][0]["possible_boundary_clipping"] is True
        for problem in issues["problems"]
    )


def test_candidate_independent_detours_include_mapped_route_geometry() -> None:
    data = fixture_snapshot()
    graph = data.graphs["walk"]
    positions = {1: (27.580, 47.162), 2: (27.580, 47.165), 3: (27.5801, 47.162)}
    for node, coordinate in positions.items():
        _set_wgs84(graph, data.area, node, coordinate)
    for left, right, _key, attrs in graph.edges(keys=True, data=True):
        start, end = graph.nodes[left], graph.nodes[right]
        geometry = LineString([(start["x"], start["y"]), (end["x"], end["y"])])
        attrs["geometry"] = geometry
        attrs["length_m"] = geometry.length
        attrs["length"] = geometry.length
    analysis = analyze_snapshot(data)
    issues = detect_urban_problems(
        data, analysis=analysis, route_pair_sample_count=128,
        min_direct_distance_m=1, detour_ratio_threshold=2.0,
    )
    detour = next(item for item in issues["problems"] if item["problem_type"] == "excessive_pedestrian_detour")
    evidence = detour["evidence"][0]
    assert evidence["network_distance_m"] > evidence["direct_distance_m"]
    assert evidence["detour_ratio"] >= 2.0
    assert evidence["units"] == {"network_distance_m": "m", "direct_distance_m": "m", "detour_ratio": "ratio"}
    assert detour["geometry_meaning"] == "actual_mapped_graph_edge_path"
    assert detour["geometry"]["type"] == "LineString"


def test_access_issues_require_available_mapped_destinations_and_empty_layers_stay_unknown() -> None:
    data = fixture_snapshot()
    data.layers["schools"] = gpd.GeoDataFrame(
        {"osm_id": ["school-1"], "amenity": ["school"]},
        geometry=[Point(27.5767, 47.162)], crs="EPSG:4326",
    )
    data.layer_availability["schools"] = {"status": "available", "feature_count": 1}
    data.metadata["feature_category_availability"] = {"schools": {"status": "available", "feature_count": 1, "source_query": {"amenity": "school"}}}
    analysis = analyze_snapshot(data)
    issues = detect_urban_problems(data, analysis=analysis, route_pair_sample_count=16)
    assert any(problem["problem_type"] == "weak_access_to_mapped_destination" for problem in issues["problems"])

    empty = fixture_snapshot()
    empty.metadata["feature_category_availability"] = {"schools": {"status": "available_but_empty", "feature_count": 0}}
    empty_issues = detect_urban_problems(empty, analysis=analyze_snapshot(empty), route_pair_sample_count=8)
    assert not any(problem["problem_type"] == "weak_access_to_mapped_destination" for problem in empty_issues["problems"])
    school_gap = next(item for item in empty_issues["coverage_gaps"] if item["category_id"] == "schools")
    assert school_gap["status"] == "available_but_empty"
    assert "does not establish" in school_gap["interpretation"]


def test_invalid_graph_and_issue_geometry_are_skipped_without_mutating_baseline() -> None:
    data = fixture_snapshot()
    analysis = analyze_snapshot(data)
    graph = data.graphs["walk"]
    original_nodes, original_edges = graph.number_of_nodes(), graph.number_of_edges()
    graph.add_node("bad", x=math.nan, y=47.16)
    malformed = copy.deepcopy(analysis)
    malformed["issues"].append({"id": "bad-geometry", "type": "walk_poor_access_to_schools", "geometry": {"type": "Point", "coordinates": [999, 47]}, "metrics": {}})
    result = detect_urban_problems(data, analysis=malformed, route_pair_sample_count=8)
    assert all(problem["problem_id"] != "bad-geometry" for problem in result["problems"])
    geojson = problem_locations_geojson(result)
    assert geojson["type"] == "FeatureCollection"
    assert graph.number_of_nodes() == original_nodes + 1
    assert graph.number_of_edges() == original_edges


def test_live_osm_top_level_source_geometry_hash_is_verified() -> None:
    data = fixture_snapshot()
    analysis = analyze_snapshot(data)
    data.metadata["source"] = "OpenStreetMap"
    data.metadata["source_version"] = "osm-snapshot-test"
    data.metadata["source_area_geometry_sha256"] = detect_urban_problems(data, analysis=analysis)["area_geometry_sha256"]
    issues = detect_urban_problems(data, analysis=analysis, route_pair_sample_count=8)
    assert issues["source_area_verification"] == "verified"
    assert issues["data_confidence"] == "limited"


def test_missing_network_and_unverified_sumo_never_become_traffic_problems() -> None:
    data = fixture_snapshot()
    data.graphs.clear()
    analysis = analyze_snapshot(data)
    fake_pair = {
        "status": "completed",
        "study_area": {"area_id": data.area.area_id},
        "source": {"source_area": {}},
        "source_area_verification": {"status": "verified"},
        "comparison": {"metrics": {"duration": {"baseline_mean": 60, "scenario_mean": 1, "scenario_minus_baseline_mean": -59}}},
        "baseline": {"status": "completed"},
        "scenario": {"status": "completed"},
        "baseline_run_id": "fake-base",
        "scenario_run_id": "fake-scenario",
    }
    issues = detect_urban_problems(data, analysis=analysis, paired_sumo_result=fake_pair, route_pair_sample_count=8)
    assert issues["problems"] == []
    assert issues["simulation_observations"] == []
    assert issues["simulation_status"]["status"] == "rejected_unverified_source_or_pair"
    assert "No usable walking graph" in " ".join(issues["warnings"])


def test_supported_candidates_copy_authoritative_geometry_and_separate_targeted_diagnostics(planning_case: dict) -> None:
    candidates = {item["candidate_id"]: item for item in planning_case["evaluation"]["ranked_candidates"]}
    options = [item for item in planning_case["plan"]["solutions"] if item["status"] == "supported_evaluated"]
    assert options
    for option in options:
        candidate = candidates[option["candidate_id"]]
        assert option["geometry"] == candidate["geometry"]
        assert option["intervention"] == candidate["intervention"]
        assert option["shared_sample_impact"]["aggregate"] == candidate["impact"]["aggregate"]
        assert option["shared_sample_impact"]["used_for_ranking"] is True
        if candidate.get("targeted_diagnostic_impact"):
            assert option["targeted_diagnostic_impact"]["used_for_ranking"] is False
    assert any(item["shared_sample_impact"]["aggregate"]["improved_count"] == 0 for item in options)


def test_concepts_have_no_fake_geometry_or_metrics_and_empty_candidate_pool_is_honest() -> None:
    data = fixture_snapshot()
    analysis = analyze_snapshot(data)
    data.layers["buildings"] = gpd.GeoDataFrame(
        {"osm_id": ["blocks-area"]},
        geometry=[data.area.polygon], crs="EPSG:4326",
    )
    data.layer_availability["buildings"] = {"status": "available", "feature_count": 1}
    evaluation = evaluate_candidates(data, analysis=analysis, sample_count=8)
    issues = detect_urban_problems(data, analysis=analysis, candidate_evaluation=evaluation, route_pair_sample_count=8)
    plan = build_solution_plan(data, analysis, issues, evaluation)
    assert not evaluation["ranked_candidates"]
    assert plan["status"] == "no_supported_solution"
    concepts = [item for item in plan["solutions"] if item["status"] == "concept_only_not_evaluated"]
    assert concepts
    assert all(item["geometry"] is None and item["intervention"] is None and item["shared_sample_impact"] is None for item in concepts)


def test_ai_packet_is_bounded_area_bound_and_reusable_context_is_preserved(planning_case: dict) -> None:
    packet = planning_case["packet"]
    assert packet["integrity"]["serialized_bytes"] <= MAX_AI_PACKET_BYTES
    assert packet["sim_proposal_context"]["schema_version"] == "arteria.proposal-context.v1"
    assert packet["source"]["area_geometry_sha256"] == packet["urban_intelligence"]["area_geometry_sha256"]
    included_problem_ids = {item["problem_id"] for item in packet["urban_intelligence"]["problems"]}
    included_evidence_ids = {
        evidence["evidence_id"]
        for problem in packet["urban_intelligence"]["problems"]
        for evidence in (problem["evidence"] if isinstance(problem.get("evidence"), list) else [])
    }
    included_evidence_ids.update(item["gap_id"] for item in packet["urban_intelligence"]["coverage_gaps"])
    included_evidence_ids.update(item["observation_id"] for item in packet["urban_intelligence"]["simulation_observations"])
    for solution in packet["solution_plan"]["solutions"]:
        assert set(solution["problem_ids"]).issubset(included_problem_ids)
        assert set(solution["evidence_ids"]).issubset(included_evidence_ids)
    json.dumps(packet, ensure_ascii=False, allow_nan=False)
    wrong_area = copy.deepcopy(planning_case["issues"])
    wrong_area["area_id"] = "wrong-area"
    with pytest.raises(ValueError, match="same study area"):
        build_ai_planning_packet(planning_case["data"], planning_case["analysis"], wrong_area, planning_case["evaluation"], planning_case["plan"])


def test_ai_contract_accepts_whitelisted_references_and_attaches_sim_authority(planning_case: dict) -> None:
    response = _valid_response(planning_case)
    result = validate_ai_planning_response(response, planning_case["packet"])
    assert result["status"] == "validated"
    recommendation = result["recommended_solutions"][0]
    assert recommendation["authoritative_sim_solution"]["solution_id"] == recommendation["solution_id"]
    expected_geometry = next(item for item in planning_case["plan"]["solutions"] if item["solution_id"] == recommendation["solution_id"])["geometry"]
    assert recommendation["authoritative_sim_solution"]["geometry"] == json.loads(json.dumps(expected_geometry))


def test_ai_contract_partially_rejects_unknown_problem_and_candidate_ids(planning_case: dict) -> None:
    response = _valid_response(planning_case)
    response["identified_problems"].append({"problem_id": "problem_unknown", "explanation": "Dovezile nu sunt disponibile.", "evidence_ids": ["evidence_unknown"]})
    bad = copy.deepcopy(response["recommended_solutions"][0])
    bad["candidate_id"] = "candidate_unknown"
    response["recommended_solutions"].append(bad)
    result = validate_ai_planning_response(response, planning_case["packet"])
    assert result["status"] == "completed_with_rejections"
    assert len(result["recommended_solutions"]) == 1
    assert {finding["code"] for finding in result["findings"]} & {"unknown_problem_id", "unknown_or_mismatched_candidate_id", "unknown_candidate_id"}


def test_ai_contract_rejects_candidate_impact_claims_that_contradict_shared_sample(planning_case: dict) -> None:
    response = _valid_response(planning_case)
    assert response["recommended_solutions"][0]["candidate_id"]
    response["recommended_solutions"][0]["explanation"] = "There is no impact or benefit from this candidate."
    result = validate_ai_planning_response(response, planning_case["packet"])
    assert any(item["code"] == "contradictory_candidate_impact_claim" for item in result["findings"])
    assert result["recommended_solutions"] == []


@pytest.mark.parametrize(
    ("field", "value", "expected_code"),
    [
        ("action_type", "build_roundabout", "forbidden_authoritative_claim_or_action"),
        ("geometry", {"type": "Point", "coordinates": [27.58, 47.16]}, "forbidden_authoritative_claim_or_action"),
        ("metrics", {"time_saved_s": 12}, "forbidden_authoritative_claim_or_action"),
        ("cost", 1000, "forbidden_authoritative_claim_or_action"),
        ("citations", ["https://example.com"], "forbidden_authoritative_claim_or_action"),
        ("sumo_run_id", "sumo_run_fake", "forbidden_authoritative_claim_or_action"),
        ("physical_feasibility", "buildable", "forbidden_authoritative_claim_or_action"),
    ],
)
def test_ai_contract_rejects_model_authored_authoritative_fields(planning_case: dict, field: str, value: object, expected_code: str) -> None:
    response = _valid_response(planning_case)
    response["recommended_solutions"][0][field] = value
    result = validate_ai_planning_response(response, planning_case["packet"])
    assert result["status"] == "completed_with_rejections"
    assert result["recommended_solutions"] == []
    assert any(item["code"] == expected_code for item in result["findings"])


def test_ai_contract_rejects_numeric_claims_wrong_area_stale_packet_and_bad_json(planning_case: dict) -> None:
    response = _valid_response(planning_case)
    response["recommended_solutions"][0]["explanation"] = "This will reduce travel by 20 percent."
    assert "untrusted_numeric_or_citation_claim" in {item["code"] for item in validate_ai_planning_response(response, planning_case["packet"])["findings"]}
    response = _valid_response(planning_case)
    response["area_id"] = "other-area"
    assert validate_ai_planning_response(response, planning_case["packet"])["status"] == "rejected"
    corrupted = copy.deepcopy(planning_case["packet"])
    corrupted["urban_intelligence"]["problems"][0]["description"] += " changed"
    assert validate_ai_planning_response(_valid_response(planning_case), corrupted)["findings"][0]["code"] == "invalid_or_corrupted_evidence_packet"
    stale = _valid_response(planning_case)
    stale["evidence_packet_sha256"] = "0" * 64
    assert validate_ai_planning_response(stale, planning_case["packet"])["findings"][0]["code"] == "wrong_area_or_stale_packet"
    assert validate_ai_planning_response("{not json", planning_case["packet"])["status"] == "rejected"
    assert validate_ai_planning_response("{" + " " * 20_000, planning_case["packet"])["findings"][0]["code"] == "response_too_large"
    nonfinite = _valid_response(planning_case)
    nonfinite["unexpected"] = math.nan
    assert validate_ai_planning_response(nonfinite, planning_case["packet"])["status"] == "rejected"


def test_provider_adapter_handles_missing_timeout_error_and_mock_success(planning_case: dict) -> None:
    packet = planning_case["packet"]
    assert run_ai_planning(packet, None)["status"] == "provider_unavailable"

    def timeout(**_kwargs):
        time.sleep(0.1)

    assert run_ai_planning(packet, timeout, timeout_seconds=0.01)["status"] == "timeout"

    def fail(**_kwargs):
        raise RuntimeError("provider failed")

    assert run_ai_planning(packet, fail)["status"] == "provider_error"
    result = run_ai_planning(packet, lambda **_kwargs: _valid_response(planning_case))
    assert result["status"] == "completed"
    assert result["ai_generated"] is True


def test_planning_demo_is_offline_mock_labeled_and_writes_required_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_acquire(*_args, **_kwargs):
        raise AssertionError("fixture planning demo must not make an OSM request")

    monkeypatch.setattr("sim.mvp_demo.acquire_osm_data", forbidden_acquire)
    result = run_mvp_demo(source="fixture", output_dir=tmp_path / "planning", planning=True)
    assert result["mock_ai"]["provider"] == "deterministic_mock"
    assert result["mock_ai"]["live_cloud_inference"] is False
    assert result["mock_ai"]["validation"]["status"] == "validated"
    expected = {
        "analysis.json", "urban_problems.json", "solutions.json", "ai_evidence_packet.json", "ai_input_example.json",
        "ai_output_schema.json", "candidate_evidence.geojson", "problem_locations.geojson", "summary.md", "validation_report.json",
    }
    assert expected.issubset({item.name for item in (tmp_path / "planning").iterdir()})
    packet_text = (tmp_path / "planning" / "ai_evidence_packet.json").read_text(encoding="utf-8")
    packet = json.loads(packet_text)
    assert packet["integrity"]["serialized_bytes"] <= MAX_AI_PACKET_BYTES
    assert len(json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")) == packet["integrity"]["serialized_bytes"]
    assert "mock" in (tmp_path / "planning" / "summary.md").read_text(encoding="utf-8").casefold()
    assert AI_OUTPUT_SCHEMA["additionalProperties"] is False
    assert "cloud" in AI_SYSTEM_PROMPT.casefold()


def test_package_exports_existing_backend_compatible_entry_points() -> None:
    assert callable(acquire_osm_data)
    assert callable(analyze_snapshot)
    assert callable(evaluate_candidates)
