"""Regression cases found in the backend audit; all storage is temporary."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import subprocess

from fastapi.testclient import TestClient
import pytest

from backend.main import app
from backend.spatial_adapter import SpatialAdapter

client = TestClient(app, raise_server_exceptions=False)


def engine_result():
    return {
        "analysis": {"analysis_id": "analysis-test", "area": {"area_id": "fixture"},
                     "created_at": "2026-10-17T00:00:00Z", "indicators": [], "issues": [],
                     "provenance": {"source": "synthetic offline fixture"}, "warnings": []},
        "alternatives": {"schema_version": 1, "warnings": [], "ranked_candidates": [{
            "candidate_id": "c1", "intervention": {"type": "add_pedestrian_connection", "start": [27.58,47.16], "end": [27.581,47.16]},
            "evaluation_rationale": ["A hypothetical graph link"], "ranking_explanation": "Shared sample", "rank": 1,
            "impact": {"aggregate": {"evaluated_pair_count": 1, "improved_count": 0, "regressed_count": 1,
                                     "newly_reachable_count": 0, "newly_unreachable_count": 0, "total_distance_savings_m": -10.0},
                       "routes": [{"origin_node_id": "1", "destination_node_id": "2", "outcome": "regressed",
                                   "before": {"status": "reachable", "network_distance_m": 10.0, "estimated_walk_time_s": 8.0},
                                   "after": {"status": "reachable", "network_distance_m": 20.0, "estimated_walk_time_s": 16.0},
                                   "distance_delta_m": 10.0}],
                       "provenance": {"source": "synthetic-test"}, "warnings": []},
        }]},
        "proposal_options": [{"candidate_id": "c1", "summary": "Candidate-backed test proposal"}],
        "proposal_validation": {"status": "all_candidate_backed_evaluated",
                                "summary": {"submitted_count": 1, "accepted_count": 1, "rejected_count": 0, "duplicate_count": 0},
                                "results": [{"candidate_id": "c1", "status": "candidate_backed_evaluated",
                                             "physical_feasibility": "unknown", "findings": []}]},
        "evidence_packet": {"schema_version": "arteria.proposal-context.v1"},
    }


def mock_worker(monkeypatch, tmp_path, payload):
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "records.sqlite3"))
    monkeypatch.setattr(SpatialAdapter, "configuration", lambda self: (tmp_path, "test"))
    output = payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr("backend.spatial_adapter.subprocess.run", lambda *a, **kw: subprocess.CompletedProcess([], 0, output, ""))


@pytest.mark.parametrize("defect", ["missing_id", "wrong_candidate", "missing_intervention", "bad_coordinate", "missing_impact", "bad_aggregate", "missing_route_id", "bad_route_delta", "missing_rationale", "duplicate_ids", "bad_analysis", "nonfinite"])
def test_bad_engine_result_is_rejected_before_storage(monkeypatch, tmp_path, defect):
    payload = engine_result()
    candidate = payload["alternatives"]["ranked_candidates"][0]
    if defect == "missing_id": candidate.pop("candidate_id")
    elif defect == "wrong_candidate": payload["alternatives"]["ranked_candidates"] = [None]
    elif defect == "missing_intervention": candidate.pop("intervention")
    elif defect == "bad_coordinate": candidate["intervention"]["start"] = [999.0, 47.0]
    elif defect == "missing_impact": candidate.pop("impact")
    elif defect == "bad_aggregate": candidate["impact"]["aggregate"]["improved_count"] = "many"
    elif defect == "missing_route_id": candidate["impact"]["routes"][0].pop("origin_node_id")
    elif defect == "bad_route_delta": candidate["impact"]["routes"][0]["distance_delta_m"] = []
    elif defect == "missing_rationale": candidate.pop("evaluation_rationale")
    elif defect == "duplicate_ids": payload["alternatives"]["ranked_candidates"].append(deepcopy(candidate))
    elif defect == "bad_analysis": payload["analysis"] = {}
    elif defect == "nonfinite": candidate["impact"]["aggregate"]["total_distance_savings_m"] = float('nan')
    mock_worker(monkeypatch, tmp_path, payload)
    r = client.post('/api/v1/spatial/studies', json={})
    assert r.status_code == 502, r.text
    assert r.json()["error"]["code"] == "spatial_failure"
    db = tmp_path / "records.sqlite3"
    if db.exists():
        with sqlite3.connect(db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 0


def test_valid_engine_extensions_and_negative_impacts_survive(monkeypatch, tmp_path):
    payload = engine_result()
    payload["alternatives"]["ranked_candidates"][0]["future_metadata"] = {"retain": [1, 2]}
    mock_worker(monkeypatch, tmp_path, payload)
    r = client.post('/api/v1/spatial/studies', json={})
    assert r.status_code == 201, r.text
    study = r.json()
    assert study["analysis"] == payload["analysis"]
    assert study["alternatives"] == payload["alternatives"]
    assert study["proposal_validation"]["results"][0]["status"] == "candidate_backed_evaluated"
    c = payload["alternatives"]["ranked_candidates"][0]
    e = client.post(f"/api/v1/spatial/studies/{study['study_id']}/evaluate", json={"baseline_id": study["baseline_id"], "candidate_id": c["candidate_id"], "intervention": c["intervention"]})
    assert e.status_code == 200
    assert e.json()["impact"] == c["impact"]


@pytest.mark.parametrize("failure", ["parent_is_file", "database_is_directory", "corrupt_database"])
def test_storage_failures_have_safe_error_envelope(monkeypatch, tmp_path, failure):
    path = tmp_path / "private-database"
    if failure == "parent_is_file":
        path.write_text('existing user file')
        path = path / "db.sqlite3"
    elif failure == "database_is_directory": path.mkdir()
    else: path.write_bytes(b'not a SQLite database')
    monkeypatch.setenv("ARTERIA_DB_PATH", str(path))
    for response in [client.post('/analyze', json={"area":{"area_id":"copou"}}), client.get('/analyses/missing')]:
        assert response.status_code == 503, response.text
        error = response.json()["error"]
        assert error["code"] == "storage_unavailable"
        assert error["request_id"]
        assert str(tmp_path) not in response.text
    assert client.get('/health').status_code == 200  # liveness contract is unchanged


def test_engine_with_no_candidates_remains_valid(monkeypatch, tmp_path):
    payload = engine_result()
    payload["alternatives"]["ranked_candidates"] = []
    mock_worker(monkeypatch, tmp_path, payload)
    response = client.post('/api/v1/spatial/studies', json={})
    assert response.status_code == 201, response.text
    study = response.json()
    response = client.get(f"/api/v1/spatial/studies/{study['study_id']}/candidates")
    assert response.status_code == 200
    assert response.json()["candidates"] == []
