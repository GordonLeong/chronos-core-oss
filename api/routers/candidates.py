from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.candidate_engine import generate_candidates_for_template
from db import get_session
from models import CandidateCreate, CandidateRead, CandidateStatus, GenerateCandidateRequest, GenerateCandidateResponse
from repositories.candidates import create_candidate, list_candidates_for_universe, update_candidate_status
from repositories.universes import get_universe_by_id
from pydantic import BaseModel




router = APIRouter(prefix="/candidates", tags=["candidates"])
class CandidateStatusUpdate(BaseModel):
    status: CandidateStatus
    reason_code: str | None = None

@router.post("", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
async def create_candidate_endpoint(
    payload: CandidateCreate,
    session: AsyncSession = Depends(get_session),
) -> CandidateRead:
    row = await create_candidate(session, payload)
    return CandidateRead.model_validate(row)


@router.get("", response_model=list[CandidateRead])
async def list_candidates_endpoint(
    universe_id: int = Query(..., ge=1),
    status: CandidateStatus | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[CandidateRead]:
    rows = await list_candidates_for_universe(
        session,
        universe_id=universe_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [CandidateRead.model_validate(r) for r in rows]

@router.patch("/{candidate_id}/status", response_model=CandidateRead)
async def update_candidate_status_endpoint(
    candidate_id: int,
    payload: CandidateStatusUpdate,
    session: AsyncSession = Depends(get_session),
) -> CandidateRead:
    row = await update_candidate_status(
        session,
        candidate_id=candidate_id,
        status=payload.status,
        reason_code=payload.reason_code,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    return CandidateRead.model_validate(row)


@router.post("/generate", response_model=GenerateCandidateResponse, status_code=status.HTTP_201_CREATED)
async def generate_candidates_endpoint(
    payload: GenerateCandidateRequest,
    session: AsyncSession = Depends(get_session),
) -> GenerateCandidateResponse:
    u = await get_universe_by_id(session, payload.universe_id)
    if u is None:
        raise HTTPException(status_code=404, detail = "universe not found")
    
    try:
        created = await generate_candidates_for_template(
            session,
            universe_id=payload.universe_id,
            template_id=payload.template_id,
            provider=payload.provider,
            interval=payload.interval,
        )

    except ValueError as exc:
            if str(exc) == "template not found":
                raise HTTPException(status_code=404, detail="template not found")
            raise HTTPException(status_code=400, detail=str(exc))
    return GenerateCandidateResponse(
        universe_id=payload.universe_id,
        template_id=payload.template_id,
        created_count=created,
    )