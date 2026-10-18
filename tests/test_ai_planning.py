"""Backend integration tests for SIM-grounded AI planning."""

from __future__ import annotations

from copy import deepcopy
import json
import sqlite3

import httpx
import pytest
from fastapi.testclient import TestClient

import sim
from backend.ai_planning_models import AIPlanningResult
from backend.ai_planning_routes import studies
from backend.ai_planning_storage import PlanningRepository
from backend.ai_provider import (
    MAX_PROVIDER_RESPONSE_BYTES,
    OpenAIResponsesProvider,
    ProviderSelection,
    resolve_provider,
)
from backend.main import app
from backend.settings import Settings
from backend.spatial_models import Study
from backend.spatial_worker import calculate

client = TestClient(app)


def sim_fixture_result():
    from sim.demo import fixture_snapshot

    snapshot = fixture_snapshot()
    analysis = sim.analyze_snapshot(snapshot)
    evaluation = sim.evaluate_candidates(
        snapshot, analysis=analysis, sample_count=16, seed="planning-tests",
        max_candidates=3, max_evaluated_candidates=6,
        candidate_pool_limit=30, route_geometry_limit=16,
    )
    options = sim.prepare_candidate_options(analysis, evaluation)
    proposal_validation = sim.validate_proposal_set(options, data=snapshot, candidate_evaluation=evaluation)
    evidence_packet = sim.build_proposal_context(snapshot, analysis, evaluation)
    urban = sim.detect_urban_problems(snapshot, analysis=analysis, candidate_evaluation=evaluation)
    solution_plan = sim.build_solution_plan(snapshot, analysis, urban, evaluation)
    ai_packet = sim.build_ai_planning_packet(snapshot, analysis, urban, evaluation, solution_plan)
    return {
        "analysis": analysis,
        "alternatives": evaluation,
        "proposal_options": options,
        "proposal_validation": proposal_validation,
        "evidence_packet": evidence_packet,
        "urban_issues": urban,
        "solution_plan": solution_plan,
        "ai_evidence_packet": ai_packet,
        "problem_locations_geojson": sim.problem_locations_geojson(urban),
    }


@pytest.fixture
def stored_study(monkeypatch, tmp_path):
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "planning.sqlite3"))
    engine_result = sim_fixture_result()
    monkeypatch.setattr(
        "backend.spatial_routes.engine.run",
        lambda body: (deepcopy(engine_result), "planning-test-revision"),
    )
    response = client.post("/api/v1/spatial/studies", json={"source": "fixture"})
    assert response.status_code == 201, response.text
    json_engine_result = json.loads(json.dumps(engine_result, ensure_ascii=False, allow_nan=False))
    return response.json(), json_engine_result


def valid_model_response(packet):
    urban = packet["urban_intelligence"]
    plan = packet["solution_plan"]
    response = {
        "schema_version": "arteria.ai-planning-response.v1",
        "area_id": urban["area_id"],
        "evidence_packet_sha256": packet["integrity"]["sha256"],
        "summary": "Dovezile cartografiate susțin o verificare suplimentară în teren.",
        "identified_problems": [],
        "recommended_solutions": [],
        "supported_candidate_ids": [],
        "evidence_references": [],
        "limitations": ["Datele mapate pot fi incomplete."],
        "requires_field_verification": True,
    }
    if urban.get("problems"):
        problem = urban["problems"][0]
        evidence_ids = [item["evidence_id"] for item in problem.get("evidence", []) if item.get("evidence_id")]
        if evidence_ids:
            response["identified_problems"] = [{
                "problem_id": problem["problem_id"],
                "explanation": "Graful sugerează o posibilă discontinuitate care necesită verificare pe teren.",
                "evidence_ids": evidence_ids[:1],
            }]
            response["evidence_references"].extend(evidence_ids[:1])
    if plan.get("solutions"):
        solution = plan["solutions"][0]
        problem_ids = list(solution.get("problem_ids", []))
        evidence_ids = list(solution.get("evidence_ids", []))
        response["recommended_solutions"] = [{
            "solution_id": solution["solution_id"],
            "candidate_id": solution.get("candidate_id"),
            "problem_ids": problem_ids,
            "title": "Verificarea opțiunii documentate de SIM",
            "explanation": "Opțiunea se bazează pe dovezile citate; verificarea fizică rămâne necesară.",
            "expected_benefit_type": solution["expected_benefit_type"],
            "evidence_ids": evidence_ids,
            "field_verification_required": True,
        }]
        response["supported_candidate_ids"] = [solution["candidate_id"]] if solution.get("candidate_id") else []
        response["evidence_references"].extend(evidence_ids)
    response["evidence_references"] = list(dict.fromkeys(response["evidence_references"]))
    return response


def configured_callback(callback, model="gpt-test"):
    return ProviderSelection(callback, "openai", model, 3.0)


def test_study_persists_urban_outputs_and_packet(stored_study):
    study, generated = stored_study
    assert study["urban_issues"] == generated["urban_issues"]
    assert study["solution_plan"] == generated["solution_plan"]
    assert study["ai_evidence_packet"] == generated["ai_evidence_packet"]
    assert study["problem_locations_geojson"] == generated["problem_locations_geojson"]
    assert study["evidence_packet_sha256"] == generated["ai_evidence_packet"]["integrity"]["sha256"]
    assert study["ai_evidence_packet"]["study_area"]["area_id"] == study["ai_evidence_packet"]["urban_intelligence"]["area_id"]


def test_legacy_stored_study_remains_readable(monkeypatch, tmp_path):
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "legacy.sqlite3"))
    legacy_payload = {
        "study_id": "study_legacy", "baseline_id": "graph_legacy",
        "created_at": "2026-01-01T00:00:00Z", "source": "fixture",
        "engine_revision": "old-revision", "calculation": "pedestrian_graph",
        "analysis": {}, "alternatives": {}, "proposal_options": [],
        "proposal_validation": {}, "evidence_packet": {}, "warnings": [],
    }
    with studies.connection() as conn:
        with conn:
            conn.execute("INSERT INTO records VALUES (?, ?, ?)",
                         (studies.namespace, "study_legacy", json.dumps(legacy_payload)))
    loaded = client.get("/api/v1/spatial/studies/study_legacy")
    assert loaded.status_code == 200
    assert loaded.json()["urban_issues"] == {}
    assert loaded.json()["ai_evidence_packet"] == {}
    assert loaded.json()["evidence_packet_sha256"] is None


def test_missing_credentials_returns_explicit_unavailable_result_and_retrieves(
    stored_study, monkeypatch,
):
    study, _ = stored_study
    monkeypatch.setenv("ARTERIA_AI_ENABLED", "true")
    monkeypatch.delenv("ARTERIA_AI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = client.post(f"/api/v1/spatial/studies/{study['study_id']}/planning", json={})
    assert result.status_code == 200, result.text
    payload = result.json()
    assert payload["provider_status"] == "provider_unavailable"
    assert payload["error_code"] == "missing_provider_credentials"
    assert payload["ai_generated"] is False
    assert payload["provider"] is None and payload["model_id"] is None
    assert payload["recommended_solutions"] == []
    retrieved = client.get(
        f"/api/v1/spatial/studies/{study['study_id']}/planning/{payload['planning_id']}"
    )
    assert retrieved.status_code == 200
    assert retrieved.json() == payload


def test_missing_key_is_distinct_from_disabled_provider(monkeypatch):
    configured = Settings(
        cors_origins=[], ai_enabled=True, ai_provider="openai", ai_model="gpt-test",
        ai_api_key=None, ai_base_url="https://api.openai.com/v1", ai_timeout_seconds=4,
    )
    selection = resolve_provider(configured)
    assert selection.call_model is None
    assert selection.unavailable_code == "missing_provider_credentials"


def test_unsupported_provider_is_unavailable(monkeypatch):
    configured = Settings(
        cors_origins=[], ai_enabled=True, ai_provider="not-supported", ai_model="gpt-test",
        ai_api_key="test-secret", ai_base_url="https://api.openai.com/v1", ai_timeout_seconds=4,
    )
    selection = resolve_provider(configured)
    assert selection.call_model is None
    assert selection.unavailable_code == "unsupported_provider"


def test_validated_cloud_response_uses_authoritative_sim_solution_and_is_idempotent(
    stored_study, monkeypatch,
):
    study, _ = stored_study
    calls = []

    def callback(**kwargs):
        calls.append(kwargs)
        return json.dumps(valid_model_response(kwargs["packet"]), ensure_ascii=False)

    monkeypatch.setattr("backend.ai_planning_service.resolve_provider", lambda: configured_callback(callback))
    key = {"Idempotency-Key": "test-planning-001"}
    endpoint = f"/api/v1/spatial/studies/{study['study_id']}/planning"
    first = client.post(endpoint, json={}, headers=key)
    assert first.status_code == 200, first.text
    result = first.json()
    assert result["provider_status"] == "completed"
    assert result["ai_generated"] is True
    assert result["provider"] == "openai" and result["model_id"] == "gpt-test"
    assert result["validation"]["status"] == "validated"
    assert result["identified_problems"]
    assert result["recommended_solutions"]
    solution = result["recommended_solutions"][0]["authoritative_sim_solution"]
    assert solution["solution_id"] == result["recommended_solutions"][0]["solution_id"]
    source_solution = next(
        item for item in study["ai_evidence_packet"]["solution_plan"]["solutions"]
        if item["solution_id"] == solution["solution_id"]
    )
    assert solution["candidate_id"] == source_solution["candidate_id"]
    assert result["baseline_id"] == study["baseline_id"]
    assert result["evidence_packet_sha256"] == study["evidence_packet_sha256"]
    assert "test-secret" not in first.text

    replay = client.post(endpoint, json={}, headers=key)
    assert replay.status_code == 200
    assert replay.json() == result
    assert len(calls) == 1

    restarted_repository = PlanningRepository()
    saved = restarted_repository.get(result["planning_id"])
    assert saved is not None
    assert saved.model_dump(mode="json") == result


def test_unknown_study_and_cross_study_result_are_404(stored_study):
    study, _ = stored_study
    assert client.post("/api/v1/spatial/studies/missing/planning", json={}).status_code == 404
    created = client.post(f"/api/v1/spatial/studies/{study['study_id']}/planning", json={}).json()
    other = client.get(f"/api/v1/spatial/studies/other/planning/{created['planning_id']}")
    assert other.status_code == 404


def test_invalid_packet_is_rejected_before_provider_call(stored_study, monkeypatch):
    study, _ = stored_study
    saved = studies.get(study["study_id"])
    saved.ai_evidence_packet["integrity"]["sha256"] = "0" * 64
    monkeypatch.setattr("backend.ai_planning_routes.studies.get", lambda _: saved)

    def fail():
        pytest.fail("Provider resolution must not run for a corrupted packet")

    monkeypatch.setattr("backend.ai_planning_service.resolve_provider", fail)
    response = client.post(f"/api/v1/spatial/studies/{study['study_id']}/planning", json={})
    assert response.status_code == 409
    assert "hash" in response.json()["error"]["message"].lower()


def test_empty_body_is_allowed_but_client_authored_instructions_are_rejected(stored_study):
    study, _ = stored_study
    empty = client.post(f"/api/v1/spatial/studies/{study['study_id']}/planning")
    assert empty.status_code == 200
    rejected = client.post(
        f"/api/v1/spatial/studies/{study['study_id']}/planning",
        json={"prompt": "invent a construction cost"},
    )
    assert rejected.status_code == 422


def test_sim_validator_rejects_unknown_ids_hash_and_authoritative_claims(stored_study):
    study, _ = stored_study
    packet = study["ai_evidence_packet"]
    response = valid_model_response(packet)

    fake_id = deepcopy(response)
    fake_id["identified_problems"] = [{
        "problem_id": "invented-problem", "explanation": "O posibilă discontinuitate necesită verificare pe teren.",
        "evidence_ids": ["invented-evidence"],
    }]
    result = sim.validate_ai_planning_response(fake_id, packet)
    assert result["status"] == "completed_with_rejections"
    assert "unknown_problem_id" in {item["code"] for item in result["findings"]}

    wrong_hash = deepcopy(response)
    wrong_hash["evidence_packet_sha256"] = "f" * 64
    result = sim.validate_ai_planning_response(wrong_hash, packet)
    assert result["status"] == "rejected"

    wrong_schema = deepcopy(response)
    wrong_schema["schema_version"] = "arteria.ai-planning-response.v0"
    result = sim.validate_ai_planning_response(wrong_schema, packet)
    assert result["status"] == "rejected"

    fabricated = deepcopy(response)
    fabricated["recommended_solutions"][0]["geometry"] = {"type": "Point", "coordinates": [0, 0]}
    result = sim.validate_ai_planning_response(fabricated, packet)
    assert "forbidden_authoritative_claim_or_action" in {item["code"] for item in result["findings"]}

    invented_evidence = deepcopy(response)
    invented_evidence["identified_problems"][0]["evidence_ids"] = ["ev_invented"]
    result = sim.validate_ai_planning_response(invented_evidence, packet)
    assert "unknown_or_unrelated_evidence_id" in {item["code"] for item in result["findings"]}

    unsupported_claim = deepcopy(response)
    unsupported_claim["identified_problems"][0]["explanation"] = "The project is approved for construction."
    result = sim.validate_ai_planning_response(unsupported_claim, packet)
    assert "unsupported_physical_or_observed_claim" in {item["code"] for item in result["findings"]}

    partial = deepcopy(response)
    partial["identified_problems"].append({
        "problem_id": "invented-problem",
        "explanation": "O posibilă întrerupere necesită verificare în teren.",
        "evidence_ids": ["ev_invented"],
    })
    outcome = sim.run_ai_planning(packet, lambda **kwargs: partial, timeout_seconds=2)
    assert outcome["status"] == "completed_with_rejections"
    assert outcome["validation"]["rejected_entry_count"] == 1


@pytest.mark.parametrize("failure,expected_status", [
    ("timeout", "timeout"),
    ("provider_error", "provider_error"),
])
def test_failed_planning_does_not_change_study_or_leak_error_text(
    stored_study, monkeypatch, failure, expected_status,
):
    study, _ = stored_study

    def callback(**kwargs):
        if failure == "timeout":
            raise TimeoutError("unit-test-secret")
        raise RuntimeError("unit-test-secret")

    monkeypatch.setattr("backend.ai_planning_service.resolve_provider", lambda: configured_callback(callback))
    response = client.post(
        f"/api/v1/spatial/studies/{study['study_id']}/planning",
        json={}, headers={"Idempotency-Key": "failure-case"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["provider_status"] == expected_status
    assert result["ai_generated"] is False
    assert result["provider"] is None and result["model_id"] is None
    assert result["identified_problems"] == [] and result["recommended_solutions"] == []
    assert "unit-test-secret" not in response.text
    assert client.get(f"/api/v1/spatial/studies/{study['study_id']}").json() == study


def provider_for(handler):
    return OpenAIResponsesProvider(
        model_id="gpt-test", base_url="https://api.openai.test/v1", api_key="unit-test-secret",
        transport=httpx.MockTransport(handler),
    )


def provider_envelope(text):
    return {"status": "completed", "output": [{
        "type": "message", "content": [{"type": "output_text", "text": text}],
    }]}


def test_openai_provider_sends_sim_prompt_schema_and_returns_only_model_text(stored_study):
    study, _ = stored_study
    observed = {}

    def handler(request):
        observed["url"] = str(request.url)
        observed["authorization"] = request.headers["authorization"]
        observed["payload"] = json.loads(request.content)
        response_text = json.dumps(valid_model_response(study["ai_evidence_packet"]), ensure_ascii=False)
        return httpx.Response(200, json=provider_envelope(response_text))

    provider = provider_for(handler)
    output = provider.structured_json(
        packet=study["ai_evidence_packet"], system_prompt=sim.AI_SYSTEM_PROMPT,
        output_schema=sim.AI_OUTPUT_SCHEMA, timeout_seconds=2,
    )
    assert observed["url"] == "https://api.openai.test/v1/responses"
    assert observed["authorization"] == "Bearer unit-test-secret"
    assert observed["payload"]["text"]["format"]["schema"] == sim.AI_OUTPUT_SCHEMA
    assert observed["payload"]["text"]["format"]["strict"] is True
    assert observed["payload"]["store"] is False
    assert json.loads(output)["schema_version"] == "arteria.ai-planning-response.v1"
    assert "unit-test-secret" not in output


@pytest.mark.parametrize("failure", ["timeout", "http_error", "bad_envelope", "oversized"])
def test_provider_failures_map_to_explicit_sim_statuses(stored_study, failure):
    study, _ = stored_study

    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("provider timed out", request=request)
        if failure == "http_error":
            return httpx.Response(429, json={"error": {"message": "unit-test-secret"}})
        if failure == "bad_envelope":
            return httpx.Response(200, content=b"not-json")
        return httpx.Response(200, content=b"x" * (MAX_PROVIDER_RESPONSE_BYTES + 1))

    outcome = sim.run_ai_planning(
        study["ai_evidence_packet"], provider_for(handler).structured_json, timeout_seconds=2,
    )
    assert outcome["status"] == ("timeout" if failure == "timeout" else "provider_error")
    assert outcome["ai_generated"] is False
    assert outcome["validation"] is None
    assert "unit-test-secret" not in json.dumps(outcome)


def test_malformed_model_json_is_invalid_response(stored_study):
    study, _ = stored_study

    def handler(request):
        return httpx.Response(200, json=provider_envelope("{malformed"))

    outcome = sim.run_ai_planning(
        study["ai_evidence_packet"], provider_for(handler).structured_json, timeout_seconds=2,
    )
    assert outcome["status"] == "invalid_response"
    assert outcome["ai_generated"] is True
    assert outcome["validation"]["status"] == "rejected"


def test_oversized_or_incomplete_model_text_is_not_accepted(stored_study):
    study, _ = stored_study
    oversized = json.dumps(valid_model_response(study["ai_evidence_packet"],), ensure_ascii=False)
    oversized = oversized[:-1] + ',"extra":"' + ("x" * 17_000) + '"}'
    result = sim.run_ai_planning(study["ai_evidence_packet"], lambda **kwargs: oversized, timeout_seconds=2)
    assert result["status"] == "invalid_response"
    assert result["validation"]["findings"][0]["code"] == "response_too_large"

    def incomplete_provider(request):
        envelope = provider_envelope(json.dumps(valid_model_response(study["ai_evidence_packet"]), ensure_ascii=False))
        envelope["status"] = "incomplete"
        return httpx.Response(200, json=envelope)

    result = sim.run_ai_planning(
        study["ai_evidence_packet"], provider_for(incomplete_provider).structured_json, timeout_seconds=2,
    )
    assert result["status"] == "invalid_response"


def test_idempotency_key_is_allowed_by_browser_cors():
    response = client.options(
        "/api/v1/spatial/studies/example/planning",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,idempotency-key",
        },
    )
    assert response.status_code == 200
    assert "idempotency-key" in response.headers.get("access-control-allow-headers", "").lower()


def test_osm_worker_calls_sim_geography_and_builds_packet(monkeypatch, tmp_path):
    from sim.demo import fixture_snapshot
    snapshot = fixture_snapshot()
    seen = {}
    monkeypatch.setenv("ARTERIA_SIM_ROOT", str(__import__("backend.spatial_adapter", fromlist=["ROOT"]).ROOT))
    monkeypatch.setenv("ARTERIA_SPATIAL_CACHE", str(tmp_path))
    monkeypatch.setattr(sim, "get_neighborhood", lambda _: {"id": "test-area"})
    monkeypatch.setattr(sim, "validate_neighborhood_boundary", lambda _: {"status": "valid", "analysis_eligible": True})
    monkeypatch.setattr(sim, "neighborhood_area_input", lambda _: snapshot.area)

    def acquire(area, **kwargs):
        seen.update(kwargs)
        return snapshot

    monkeypatch.setattr(sim, "acquire_osm_data", acquire)
    output = calculate({
        "source": "osm", "neighborhood_id": "test-area", "sample_count": 16,
        "max_candidates": 3, "seed": "osm-worker-test",
    })
    assert seen["include_features"] is True
    assert seen["feature_categories"] == ("schools", "healthcare", "public_transport", "crossings")
    assert output["urban_issues"]["area_id"] == output["ai_evidence_packet"]["urban_intelligence"]["area_id"]
    assert output["solution_plan"]["area_id"] == output["ai_evidence_packet"]["study_area"]["area_id"]
    assert output["ai_evidence_packet"]["integrity"]["sha256"]
    assert output["problem_locations_geojson"]["type"] == "FeatureCollection"
