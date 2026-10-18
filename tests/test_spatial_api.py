"""API contracts and an optional real-engine offline integration check."""
from copy import deepcopy
import subprocess

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.spatial_adapter import (
    SpatialAdapter, SpatialAreaRejected, SpatialFailure, SpatialNeighborhoodNotFound, SpatialTimeout, SpatialUnavailable,
)
from backend.spatial_models import SpatialRequest

client = TestClient(app)


@pytest.fixture
def fake_engine(monkeypatch, tmp_path):
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "spatial.sqlite3"))
    result = {"analysis": {"provenance": {"source": "synthetic-test"}},
              "alternatives": {"ranked_candidates": [{
                  "candidate_id": "c1", "intervention": {"type": "add_pedestrian_connection", "start": [27.58, 47.16], "end": [27.581, 47.16]},
                  "impact": {"aggregate": {"regressed_count": 1, "improved_count": 2},
                             "routes": [{"outcome": "regressed", "distance_delta_m": 10}]}}]},
              "proposal_options": [{"candidate_id": "c1"}],
              "proposal_validation": {"results": [{"candidate_id": "c1", "status": "candidate_backed_evaluated"}]}}
    monkeypatch.setattr("backend.spatial_routes.engine.run", lambda body: (deepcopy(result), "test-revision"))
    return result


def test_spatial_selection_retains_original_impact_and_source(fake_engine):
    r = client.post("/api/v1/spatial/studies", json={"source": "fixture"})
    assert r.status_code == 201
    s = r.json()
    base = f"/api/v1/spatial/studies/{s['study_id']}"
    assert client.get(base).json() == s
    candidates = client.get(base + "/candidates").json()["candidates"]
    candidate = candidates[0]
    body = {"baseline_id": s["baseline_id"], "candidate_id": candidate["candidate_id"], "intervention": candidate["intervention"]}
    e = client.post(base + "/evaluate", json=body)
    assert e.status_code == 200
    assert e.json()["impact"] == candidate["impact"]
    assert e.json()["execution"] == "stored_graph_comparison"
    assert e.json()["evaluated_at"] == s["created_at"]
    assert e.json()["sumo_executed"] is False
    assert e.json()["source"] == "fixture"
    assert e.json()["proposal_validation"]["status"] == "candidate_backed_evaluated"
    assert client.post(base + "/evaluate", json={**body, "baseline_id": "wrong"}).status_code == 409
    assert client.post(base + "/evaluate", json={**body, "candidate_id": "wrong"}).status_code == 404
    body["intervention"]["end"] = [27.59, 47.17]
    assert client.post(base + "/evaluate", json=body).status_code == 409
    assert client.get('/api/v1/spatial/studies/missing').status_code == 404


def test_empty_candidates_are_honest(fake_engine):
    fake_engine["alternatives"]["ranked_candidates"] = []
    s = client.post("/api/v1/spatial/studies", json={}).json()
    assert s["alternatives"]["ranked_candidates"] == []


def test_candidate_must_pass_sim_validation_before_comparison(fake_engine):
    fake_engine["proposal_validation"]["results"][0]["status"] = "rejected"
    s = client.post("/api/v1/spatial/studies", json={}).json()
    candidate = s["alternatives"]["ranked_candidates"][0]
    response = client.post(f"/api/v1/spatial/studies/{s['study_id']}/evaluate", json={
        "baseline_id": s["baseline_id"], "candidate_id": candidate["candidate_id"],
        "intervention": candidate["intervention"],
    })
    assert response.status_code == 409
    assert "validation" in response.json()["error"]["message"].lower()


@pytest.mark.parametrize("body", [
    {"source": "sumo"}, {"source": "osm"},
    {"source": "fixture", "area": {"area_id": "podu-ros"}},
    {"sample_count": 65}, {"sample_count": True}, {"max_candidates": 0},
])
def test_invalid_spatial_requests_never_run_engine(body, monkeypatch):
    def fail(_):
        pytest.fail("Invalid request reached engine")
    monkeypatch.setattr("backend.spatial_routes.engine.run", fail)
    assert client.post("/api/v1/spatial/studies", json=body).status_code == 422


@pytest.mark.parametrize("failure,status,code", [
    (SpatialUnavailable, 503, "spatial_unavailable"),
    (SpatialTimeout, 504, "spatial_timeout"),
    (SpatialFailure, 502, "spatial_failure"),
])
def test_engine_errors_do_not_fall_back(monkeypatch, failure, status, code):
    def fail(_):
        raise failure("No calculation available")
    monkeypatch.setattr("backend.spatial_routes.engine.run", fail)
    r = client.post('/api/v1/spatial/studies', json={})
    assert r.status_code == status
    assert r.json()["error"]["code"] == code
    assert "analysis" not in r.json()


@pytest.mark.parametrize("failure,status,code", [
    (SpatialAreaRejected, 422, "study_area_rejected"),
    (SpatialNeighborhoodNotFound, 404, "unknown_neighborhood"),
])
def test_sourced_area_errors_are_explicit(monkeypatch, failure, status, code):
    def fail(_):
        raise failure("Rejected without downloading OSM")
    monkeypatch.setattr("backend.spatial_routes.engine.run", fail)
    response = client.post("/api/v1/spatial/studies", json={"source": "osm", "neighborhood_id": "point-only"})
    assert response.status_code == status
    assert response.json()["error"]["code"] == code


def test_missing_engine_reports_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("ARTERIA_SIM_ROOT", str(tmp_path))
    r = client.post('/api/v1/spatial/studies', json={})
    assert r.status_code == 503


def test_subprocess_timeout_is_bounded_and_releases_slot(monkeypatch, tmp_path):
    engine = SpatialAdapter()
    monkeypatch.setattr(engine, "configuration", lambda: (tmp_path, "test"))
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 90
        raise subprocess.TimeoutExpired(args[0], 90)
    monkeypatch.setattr(subprocess, "run", timeout)
    for _ in range(2):
        with pytest.raises(SpatialTimeout):
            engine.run(SpatialRequest())


def test_real_sim_engine_offline_flow(monkeypatch, tmp_path):
    """Run integrated SIM v3 fixture algorithms without network access."""
    from backend.spatial_adapter import ROOT
    root, revision = SpatialAdapter().configuration()
    assert root == ROOT
    assert revision
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "real-engine.sqlite3"))
    response = client.post('/api/v1/spatial/studies', json={"source": "fixture"})
    assert response.status_code == 201, response.text
    s = response.json()
    assert s["analysis"]["provenance"]["source"] == "synthetic offline fixture"
    assert s["alternatives"]["ranked_candidates"]
    assert s["proposal_options"]
    assert s["proposal_validation"]["summary"]["accepted_count"] == len(s["proposal_options"])
    assert s["evidence_packet"]["schema_version"] == "arteria.proposal-context.v1"
    assert s["urban_issues"]["area_id"] == s["ai_evidence_packet"]["urban_intelligence"]["area_id"]
    assert s["solution_plan"]["area_id"] == s["ai_evidence_packet"]["study_area"]["area_id"]
    assert s["problem_locations_geojson"]["type"] == "FeatureCollection"
    assert s["evidence_packet_sha256"] == s["ai_evidence_packet"]["integrity"]["sha256"]
    assert len(s["evidence_packet_sha256"]) == 64
    assert len({candidate["candidate_id"] for candidate in s["alternatives"]["ranked_candidates"]}) == len(s["alternatives"]["ranked_candidates"])
    for candidate in s["alternatives"]["ranked_candidates"]:
        e = client.post(f"/api/v1/spatial/studies/{s['study_id']}/evaluate", json={
            "baseline_id": s["baseline_id"], "candidate_id": candidate["candidate_id"],
            "intervention": candidate["intervention"]})
        assert e.status_code == 200
        assert e.json()["impact"] == candidate["impact"]
        assert e.json()["sumo_executed"] is False
        assert e.json()["proposal_validation"]["status"] == "candidate_backed_evaluated"
    assert client.get(f"/api/v1/spatial/studies/{s['study_id']}").json() == s


def test_osm_point_and_over_limit_catalog_areas_are_rejected_offline(monkeypatch, tmp_path):
    import sim

    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "area-limits.sqlite3"))
    point = next(record for record in sim.get_neighborhoods() if record["geometry_type"] == "Point")
    point_response = client.post("/api/v1/spatial/studies", json={"source": "osm", "neighborhood_id": point["id"]})
    assert point_response.status_code == 422, point_response.text
    assert point_response.json()["error"]["code"] == "study_area_rejected"

    oversized = next(record for record in sim.get_neighborhoods()
                     if sim.validate_neighborhood_boundary(record)["status"] == "requires_controlled_analysis")
    area_response = client.post("/api/v1/spatial/studies", json={"source": "osm", "neighborhood_id": oversized["id"]})
    assert area_response.status_code == 422, area_response.text
    assert area_response.json()["error"]["code"] == "study_area_rejected"
