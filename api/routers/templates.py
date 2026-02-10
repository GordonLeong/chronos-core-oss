from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query,status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from models import TemplateCreate, TemplateRead, TemplateKind
from repositories.templates import create_template, list_templates


router = APIRouter(prefix="/templates", tags=["templates"])

@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template_endpoint(
    payload: TemplateCreate,
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    try:
        row = await create_template(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return TemplateRead.model_validate(row)
    
@router.get("", response_model=list[TemplateRead])
async def list_templates_endpoint(
    kind: TemplateKind | None = Query(None),
    limit: int=Query(50, ge=1, le=200),
    offset: int=Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[TemplateRead]:
    rows = await list_templates(
        session,
        kind=kind,
        limit=limit,
        offset=offset,
    )

    return [TemplateRead.model_validate(r) for r in rows]