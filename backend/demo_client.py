"""Run an actual HTTP demo and print frontend-ready request/response pairs."""
import argparse
import json
import httpx


def run_flow(client):
    steps = []

    def post(path, body):
        response = client.post(path, json=body)
        response.raise_for_status()
        result = response.json()
        steps.append({"endpoint": path, "request": body, "response": result})
        return result

    a = post("/analyze", {
        "area": {"city_id": "iasi-ro", "area_id": "preview-podu-ros", "boundary": None,
                 "boundary_source": "known_area", "crs": "EPSG:4326"},
        "layers": ["roads", "walking", "cycling", "public_transport"],
        "analysis": {"network_modes": ["walk", "bike"],
                     "accessibility_thresholds": [{"value": 15, "unit": "minute", "mode": "walk"}]},
        "data_as_of": None,
    })
    area = {key: a["area"][key] for key in ("city_id", "area_id")}
    p = post("/propose", {"analysis_id": a["analysis_id"], "area": area,
        "issue_id": a["issues"][0]["id"], "intervention_catalog_version": "catalog-1",
        "constraints": {"max_affected_area": {"value": 3.5, "unit": "hectare"}},
        "requested_alternatives": ["minimal", "moderate", "transformative"]})
    selected = p["alternatives"][0]
    post("/evaluate", {"analysis_id": a["analysis_id"], "area": area,
        "baseline_id": a["baseline_id"], "proposal_set_id": p["proposal_set_id"],
        "alternative_level": selected["level"], "interventions": selected["interventions"],
        "evaluation": {"indicators": ["ns_delay", "ew_delay", "mean_delay"],
                       "traffic_simulation": {"requested": False, "mode": "none", "replay_id": None}}})
    return steps


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    with httpx.Client(base_url=args.base_url, timeout=15) as client:
        print(json.dumps(run_flow(client), indent=2, ensure_ascii=False))
