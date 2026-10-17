"""Exercise frontend wire shapes without altering frontend-owned files."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import AnalysisResponse
from backend.storage import Store

client = TestClient(app)


def analyze_payload(area="preview-podu-ros"):
    return {
        "area": {"city_id": "iasi-ro", "area_id": area, "boundary": None,
                 "boundary_source": "known_area", "crs": "EPSG:4326"},
        "layers": ["roads", "walking", "cycling", "public_transport"],
        "analysis": {"network_modes": ["walk", "bike"],
                     "accessibility_thresholds": [{"value": 15, "unit": "minute", "mode": "walk"}]},
        "data_as_of": None,
    }


def flow(green=None):
    r = client.post("/analyze", json=analyze_payload())
    assert r.status_code == 200, r.text
    a = r.json()
    area = {k: a["area"][k] for k in ("city_id", "area_id")}
    request = {"analysis_id": a["analysis_id"], "area": area, "issue_id": a["issues"][0]["id"],
               "intervention_catalog_version": "catalog-1",
               "constraints": {"max_affected_area": {"value": 3.5, "unit": "hectare"}},
               "requested_alternatives": ["minimal", "moderate", "transformative"]}
    if green is not None:
        request["parameters"] = {"ns_green_seconds": green}
    r = client.post("/propose", json=request)
    assert r.status_code == 200, r.text
    p = r.json()
    body = {"analysis_id": a["analysis_id"], "area": area, "baseline_id": a["baseline_id"],
            "proposal_set_id": p["proposal_set_id"], "alternative_level": "minimal",
            "interventions": p["alternatives"][0]["interventions"],
            "evaluation": {"indicators": ["ns_delay", "ew_delay", "mean_delay"],
                           "traffic_simulation": {"requested": False, "mode": "none", "replay_id": None}}}
    return a, p, body


def assert_evidence(item):
    assert set(item["uncertainty"]) == {"kind", "description", "interval", "confidence"}
    assert item["status"] == "estimated"
    for source in item["provenance"]:
        assert source["source"] == "synthetic-demo"
        assert {"source_version", "retrieved_at", "method", "crs"} <= source.keys()


def test_frontend_wire_flow_and_retrieval():
    a, p, request = flow()
    assert all(layer["status"] == "unknown" for layer in a["layer_availability"])
    for item in a["indicators"] + a["issues"]:
        assert_evidence(item)
    assert a["issues"][0]["label"]
    assert p["model"]["generated_at"]
    assert p["rejected_alternatives"] == []
    for alt in p["alternatives"]:
        assert alt["validation"]["status"] == "accepted"
        assert alt["interventions"][0]["geometry"]["type"] == "Point"
        for impact in alt["expected_impacts"]:
            assert_evidence(impact)
            assert impact["value"] is None
    r = client.post("/evaluate", json=request)
    assert r.status_code == 200, r.text
    e = r.json()
    assert e["scenario"]["intervention_catalog_version"] == "catalog-1"
    assert set(e["simulation"]) >= {"started_at", "completed_at", "configuration", "measurements"}
    for c in e["comparisons"]:
        original = next(i for i in a["indicators"] if i["id"] == c["indicator_id"])
        assert c["baseline"] == {k: v for k, v in original.items() if k not in ("id", "label")}
    for route, key, result in [("analyses", "analysis_id", a), ("proposals", "proposal_set_id", p), ("evaluations", "evaluation_id", e)]:
        assert client.get(f"/{route}/{result[key]}").json() == result
        assert client.get(f"/{route}/missing").status_code == 404
    assert client.post("/evaluate", json=request).json() == e


def test_tuning_changes_exact_parameter_and_outcome():
    outcomes = []
    for green in (20, 55):
        a, p, request = flow(green)
        e = client.post("/evaluate", json=request).json()
        assert e["scenario_inputs"]["ns_green_seconds"] == green
        assert e["baseline_inputs"] == a["inputs"]
        outcomes.append(e["comparisons"])
    assert outcomes[0] != outcomes[1]
    r = client.post("/propose", json={"analysis_id": a["analysis_id"], "parameters": {"ns_green_seconds": 75}})
    assert r.status_code == 422


def test_storage_survives_new_process():
    a, _, _ = flow()
    code = "import sys; sys.stdout.reconfigure(encoding='utf-8'); from backend.main import analyses; print(analyses.get(sys.argv[1]).model_dump_json())"
    child = subprocess.run([sys.executable, "-c", code, a["analysis_id"]], capture_output=True, text=True, encoding="utf-8", env=os.environ.copy())
    assert child.returncode == 0, f"Storage subprocess exited {child.returncode}: {child.stderr[-4000:]}"
    assert json.loads(child.stdout) == a


def test_concurrent_retries_return_one_immutable_record(tmp_path, monkeypatch):
    a, _, _ = flow()
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "concurrent.sqlite3"))
    model = AnalysisResponse.model_validate(a)
    store = Store("test", AnalysisResponse)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: store.put(a["analysis_id"], model).model_dump(), range(12)))
    assert all(result == results[0] for result in results)


@pytest.mark.parametrize("area", ["copou", "centru", "podu-ros", "tatarasi", "alexandru", "preview-copou"])
def test_bookmark_contexts_never_claim_local_measurements(area):
    r = client.post("/analyze", json=analyze_payload(area))
    assert r.status_code == 200
    assert r.json()["mode"] == "demo"
    assert all(i["status"] == "estimated" for i in r.json()["indicators"])


def test_constraints_ids_geometry_and_indicator_errors():
    a, _, body = flow()
    assert client.post("/analyze", json=analyze_payload("unrecognized")).status_code == 404
    assert client.post("/propose", json={"analysis_id": a["analysis_id"], "issue_id": "unknown"}).status_code == 404
    assert client.post("/propose", json={"analysis_id": a["analysis_id"], "constraints": {"max_affected_area": {"value": -1, "unit": "hectare"}}}).status_code == 422
    body["evaluation"]["indicators"] = ["invented_metric"]
    assert client.post("/evaluate", json=body).status_code == 422
    body["evaluation"]["indicators"] = ["ns_delay"]
    assert len(client.post("/evaluate", json=body).json()["comparisons"]) == 1
    body["interventions"][0]["geometry"]["coordinates"][0] += .01
    assert client.post("/evaluate", json=body).status_code == 409
    payload = analyze_payload()
    payload["area"]["boundary"] = {"type": "Polygon", "coordinates": [[[27.583,47.152],[27.585,47.152],[27.585,47.154],[27.583,47.154],[27.583,47.152]]]}
    assert client.post("/analyze", json=payload).status_code == 200
    payload["area"]["boundary"]["coordinates"][0].pop()
    assert client.post("/analyze", json=payload).status_code == 422


def test_nextjs_cors_and_areas():
    r = client.options("/evaluate", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
    r = client.get("/api/v1/areas")
    assert all(a["validation_status"] == "demo_bookmark" and a["bbox"] is None for a in r.json()["areas"])
    assert client.get("/api/v1/areas?city_id=other").status_code == 404


def test_capacity_errors_are_structured(monkeypatch, tmp_path):
    monkeypatch.setenv("ARTERIA_DB_PATH", str(tmp_path / "capacity.sqlite3"))
    monkeypatch.setattr("backend.main.MAX_RECORDS", 0)
    r = client.post("/analyze", json=analyze_payload())
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "capacity_unavailable"


def test_unknown_routes_and_methods_use_error_envelope():
    for response in (client.get("/not-a-route"), client.get("/analyze")):
        assert response.status_code in (404, 405)
        assert {"code", "message", "details", "request_id"} <= response.json()["error"].keys()
