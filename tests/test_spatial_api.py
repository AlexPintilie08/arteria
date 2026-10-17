"""API contracts and an optional real-engine offline integration check."""
from copy import deepcopy
import subprocess

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.spatial_adapter import SpatialAdapter, SpatialFailure, SpatialTimeout, SpatialUnavailable
from backend.spatial_models import SpatialRequest

client = TestClient(app)


@pytest.fixture
def fake_engine(monkeypatch, tmp_path):
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "spatial.sqlite3"))
    result = {"analysis": {"provenance": {"source": "synthetic-test"}},
              "alternatives": {"ranked_candidates": [{
                  "candidate_id": "c1", "intervention": {"type": "add_pedestrian_connection", "start": [27.58, 47.16], "end": [27.581, 47.16]},
                  "impact": {"aggregate": {"regressed_count": 1, "improved_count": 2},
                             "routes": [{"outcome": "regressed", "distance_delta_m": 10}]}}]}}
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
    assert client.post(base + "/evaluate", json={**body, "baseline_id": "wrong"}).status_code == 409
    assert client.post(base + "/evaluate", json={**body, "candidate_id": "wrong"}).status_code == 404
    body["intervention"]["end"] = [27.59, 47.17]
    assert client.post(base + "/evaluate", json=body).status_code == 409
    assert client.get('/api/v1/spatial/studies/missing').status_code == 404


def test_empty_candidates_are_honest(fake_engine):
    fake_engine["alternatives"]["ranked_candidates"] = []
    s = client.post("/api/v1/spatial/studies", json={}).json()
    assert s["alternatives"]["ranked_candidates"] == []


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
    """Run the colleague's algorithms, never an imitation, when configured."""
    try:
        SpatialAdapter().configuration()
    except SpatialUnavailable:
        pytest.skip("Optional sim snapshot missing; run python -m backend.prepare_sim")
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "real-engine.sqlite3"))
    response = client.post('/api/v1/spatial/studies', json={"source": "fixture"})
    assert response.status_code == 201, response.text
    s = response.json()
    assert s["analysis"]["provenance"]["source"] == "synthetic offline fixture"
    assert s["alternatives"]["ranked_candidates"]
    for candidate in s["alternatives"]["ranked_candidates"]:
        e = client.post(f"/api/v1/spatial/studies/{s['study_id']}/evaluate", json={
            "baseline_id": s["baseline_id"], "candidate_id": candidate["candidate_id"],
            "intervention": candidate["intervention"]})
        assert e.status_code == 200
        assert e.json()["impact"] == candidate["impact"]
        assert e.json()["sumo_executed"] is False
