"""Graph-only study flow, separate from the synthetic signal-timing API."""
from datetime import datetime, timezone
import json
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from backend.spatial_adapter import SpatialAdapter
from backend.spatial_models import Candidates, Selection, SpatialEvaluation, SpatialRequest, Study
from backend.storage import Store

router = APIRouter(prefix="/api/v1/spatial", tags=["pedestrian graph"])
studies = Store("spatial-studies-v1", Study)
engine = SpatialAdapter()
WARNINGS = [
    "Pedestrian graph analysis only; no traffic counts, population impacts or SUMO run.",
    "Candidate links are hypothetical and conditional; graph validity does not establish construction safety or approval.",
    "All candidate comparisons were computed together on the same baseline and shared route sample when the study was created.",
]


def load(study_id):
    result = studies.get(study_id)
    if result is None:
        raise HTTPException(404, "Unknown spatial study")
    return result


@router.post("/studies", response_model=Study, status_code=201)
def create_study(body: SpatialRequest):
    result, revision = engine.run(body)
    # The subprocess boundary emits JSON arrays. Normalize here as well so
    # strict response models behave identically when an adapter is substituted.
    result = json.loads(json.dumps(result, ensure_ascii=False, allow_nan=False))
    ai_packet = result.get("ai_evidence_packet") or {}
    integrity = ai_packet.get("integrity", {}) if isinstance(ai_packet, dict) else {}
    study = Study(study_id="study_" + uuid4().hex, baseline_id="graph_" + uuid4().hex,
        created_at=datetime.now(timezone.utc), source=body.source, engine_revision=revision,
        analysis=result["analysis"], alternatives=result["alternatives"],
        proposal_options=result.get("proposal_options", []),
        proposal_validation=result.get("proposal_validation", {}),
        evidence_packet=result.get("evidence_packet", {}),
        urban_issues=result.get("urban_issues", {}),
        solution_plan=result.get("solution_plan", {}),
        ai_evidence_packet=ai_packet,
        problem_locations_geojson=result.get("problem_locations_geojson", {}),
        evidence_packet_sha256=integrity.get("sha256") if isinstance(integrity, dict) else None,
        warnings=WARNINGS + (["Synthetic fixture, not an observation of Iași infrastructure."] if body.source == "fixture" else ["OpenStreetMap snapshot; coverage and feasibility limitations apply. Preserve ODbL attribution."]))
    return studies.put(study.study_id, study)


@router.get("/studies/{study_id}", response_model=Study)
def get_study(study_id: str):
    return load(study_id)


@router.get("/studies/{study_id}/candidates", response_model=Candidates)
def candidates(study_id: str):
    study = load(study_id)
    return Candidates(study_id=study.study_id, baseline_id=study.baseline_id,
        candidates=study.alternatives["ranked_candidates"], warnings=study.warnings)


@router.post("/studies/{study_id}/evaluate", response_model=SpatialEvaluation)
def evaluate(study_id: str, body: Selection):
    study = load(study_id)
    if body.baseline_id != study.baseline_id:
        raise HTTPException(409, "Baseline does not belong to this study")
    candidate = next((c for c in study.alternatives["ranked_candidates"] if c["candidate_id"] == body.candidate_id), None)
    if candidate is None:
        raise HTTPException(404, "Unknown candidate in this study")
    if body.intervention != candidate["intervention"]:
        raise HTTPException(409, "Intervention must match the returned candidate exactly")
    validation_results = study.proposal_validation.get("results", [])
    validation = next((item for item in validation_results
                       if isinstance(item, dict) and item.get("candidate_id") == body.candidate_id), None)
    if validation is None or validation.get("status") != "candidate_backed_evaluated":
        raise HTTPException(409, "SIM proposal validation did not approve this evaluated candidate")
    return SpatialEvaluation(study_id=study_id, baseline_id=study.baseline_id,
        candidate_id=body.candidate_id, source=study.source, evaluated_at=study.created_at,
        intervention=candidate["intervention"], impact=candidate["impact"],
        proposal_validation=validation, warnings=study.warnings)
