from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backend.main import app, analyses, proposals, evaluations

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    analyses.clear()
    proposals.clear()
    evaluations.clear()
    yield
    analyses.clear()
    proposals.clear()
    evaluations.clear()


def flow(inputs=None):
    request = {"area": {"area_id": "iasi-demo-intersection"}}
    if inputs:
        request["inputs"] = inputs
    r = client.post("/analyze", json=request)
    assert r.status_code == 200, r.text
    a = r.json()
    r = client.post("/propose", json={"analysis_id": a["analysis_id"]})
    assert r.status_code == 200, r.text
    p = r.json()
    return a, p


def evaluation(a, p, index=0):
    alt = p["alternatives"][index]
    return {"analysis_id": a["analysis_id"], "baseline_id": a["baseline_id"],
            "proposal_set_id": p["proposal_set_id"], "alternative_level": alt["level"],
            "interventions": alt["interventions"]}


def test_complete_flow_provenance_and_tradeoffs():
    a, p = flow()
    assert a["mode"] == "demo"
    assert a["provenance"][0]["source"] == "synthetic-demo"
    assert p["model"]["provider"] == "deterministic"
    baseline = deepcopy(a)
    results = []
    for i in range(3):
        r = client.post("/evaluate", json=evaluation(a, p, i))
        assert r.status_code == 200, r.text
        e = r.json()
        assert e["baseline_inputs"] == a["inputs"]
        assert e["scenario_inputs"]["ns_green_seconds"] == p["alternatives"][i]["interventions"][0]["parameters"]["ns_green_seconds"]
        assert e["simulation"]["status"] == "not_requested"
        assert {c["impact"] for c in e["comparisons"]} >= {"improved", "worsened"}
        for c in e["comparisons"]:
            assert c["delta"]["value"] == pytest.approx(c["scenario"]["value"] - c["baseline"]["value"])
            assert c["baseline"]["provenance"][0]["source"] == "synthetic-demo"
        results.append(e["comparisons"])
    assert results[0] != results[1] != results[2]
    repeated = client.post("/analyze", json={"area": {"area_id": "iasi-demo-intersection"}}).json()
    assert repeated == baseline


def test_different_baseline_parameters_are_preserved():
    a, p = flow({"cycle_seconds": 120, "ns_green_seconds": 60, "ns_demand_vph": 400, "ew_demand_vph": 900})
    e = client.post("/evaluate", json=evaluation(a, p, 2)).json()
    assert e["scenario_inputs"]["ns_green_seconds"] < 60
    for key in ("cycle_seconds", "lost_seconds", "ns_demand_vph", "ew_demand_vph"):
        assert e["scenario_inputs"][key] == a["inputs"][key]


@pytest.mark.parametrize("patch", [{"mode": "live"}, {"inputs": {"ns_green_seconds": 80}},
    {"inputs": {"ns_demand_vph": -1}}, {"area": {"city_id": "other-city", "area_id": "copou"}}, {"layers": ["unknown-layer"]}])
def test_invalid_analysis(patch):
    r = client.post("/analyze", json={"area": {"area_id": "iasi-demo-intersection"}, **patch})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_unknown_ids_and_mismatches():
    assert client.post("/propose", json={"analysis_id": "unknown"}).status_code == 404
    a, p = flow()
    body = evaluation(a, p)
    for key in ("analysis_id", "proposal_set_id"):
        assert client.post("/evaluate", json={**body, key: "unknown"}).status_code == 404
    assert client.post("/evaluate", json={**body, "baseline_id": "wrong"}).status_code == 409
    other, _ = flow({"ns_demand_vph": 800})
    assert client.post("/evaluate", json={**body, "analysis_id": other["analysis_id"], "baseline_id": other["baseline_id"]}).status_code == 409
    body["interventions"][0]["parameters"]["ns_green_seconds"] += 1
    assert client.post("/evaluate", json=body).status_code == 409
    body["interventions"][0]["parameters"]["ns_green_seconds"] = 0
    assert client.post("/evaluate", json=body).status_code == 422


def test_sumo_requests_never_fall_back():
    r = client.post("/analyze", json={"area": {"area_id": "iasi-demo-intersection"}, "mode": "sumo"})
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "sumo_unavailable"
    a, p = flow()
    for mode in ("live", "offline", "replay"):
        sim = {"requested": True, "mode": mode}
        if mode == "replay":
            sim["replay_id"] = "missing"
        r = client.post("/evaluate", json={**evaluation(a, p), "evaluation": {"traffic_simulation": sim}})
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "sumo_unavailable"


def test_docs_cors_and_malformed_json():
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert all(path in schema["paths"] for path in ("/analyze", "/propose", "/evaluate"))
    r = client.options("/analyze", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert r.status_code == 200
    assert "POST" in r.headers["access-control-allow-methods"]
    assert client.post("/analyze", content="{", headers={"Content-Type": "application/json"}).status_code == 400
