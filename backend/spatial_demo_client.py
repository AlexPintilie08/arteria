"""Run the offline graph study/candidate/evaluation flow against a live API."""
import argparse
import json
import httpx


def run_flow(client):
    response = client.post("/api/v1/spatial/studies", json={"source": "fixture"})
    response.raise_for_status()
    study = response.json()
    path = "/api/v1/spatial/studies/" + study["study_id"]
    response = client.get(path + "/candidates")
    response.raise_for_status()
    candidates = response.json()["candidates"]
    result = {"study_id": study["study_id"], "baseline_id": study["baseline_id"],
              "source": study["source"], "engine_revision": study["engine_revision"],
              "candidate_count": len(candidates), "warnings": study["warnings"], "evaluation": None}
    if candidates:
        selected = candidates[0]
        response = client.post(path + "/evaluate", json={
            "baseline_id": study["baseline_id"], "candidate_id": selected["candidate_id"],
            "intervention": selected["intervention"]})
        response.raise_for_status()
        result["evaluation"] = response.json()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    with httpx.Client(base_url=args.base_url, timeout=100) as client:
        print(json.dumps(run_flow(client), ensure_ascii=False, indent=2))
