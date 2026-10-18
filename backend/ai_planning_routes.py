"""HTTP routes that turn a stored spatial evidence packet into a plan."""

from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException

from backend.ai_planning_models import AIPlanningResult, PlanningRequest
from backend.ai_planning_service import InvalidPlanningPacket, create_planning_result, verify_study_packet
from backend.ai_planning_storage import planning_results
from backend.spatial_models import Study
from backend.storage import Store

router = APIRouter(prefix="/api/v1/spatial/studies/{study_id}/planning", tags=["AI planning"])
studies = Store("spatial-studies-v1", Study)


@router.post("", response_model=AIPlanningResult)
def create_plan(
    study_id: str,
    body: PlanningRequest | None = None,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        pattern=r"^[\x21-\x7E]{1,128}$",
    ),
):
    study = studies.get(study_id)
    if study is None:
        raise HTTPException(404, "Unknown spatial study")
    try:
        packet, packet_sha256 = verify_study_packet(study)
    except InvalidPlanningPacket as exc:
        raise HTTPException(409, str(exc)) from exc

    planning_id = "planning_" + uuid4().hex
    scoped_key = None
    if idempotency_key is not None:
        scoped_key = planning_results.idempotency_id(study_id, idempotency_key)
        state, existing_id = planning_results.claim(scoped_key, planning_id)
        if state == "complete":
            existing = planning_results.get(existing_id)
            if existing is None:
                raise HTTPException(503, "Idempotent planning result is unavailable in storage")
            return existing
        if state == "pending":
            raise HTTPException(409, "A planning request with this Idempotency-Key is still running")
        planning_id = existing_id

    result = create_planning_result(study, packet, packet_sha256, planning_id)
    if scoped_key is not None:
        return planning_results.persist_claimed(scoped_key, result)
    return planning_results.save(result)


@router.get("/{planning_id}", response_model=AIPlanningResult)
def get_plan(study_id: str, planning_id: str):
    result = planning_results.get(planning_id)
    if result is None or result.study_id != study_id:
        raise HTTPException(404, "Unknown planning result for this study")
    return result
