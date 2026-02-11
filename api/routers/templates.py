from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query,status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from models import TemplateCreate, TemplateRead, TemplateKind, TemplateUpdate
from repositories.templates import (create_template, list_templates, get_template_by_id, 
                                    delete_template, update_template, get_latest_template_by_name )


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

@router.get("/{template_id}", response_model=TemplateRead)
async def get_template_endpoint(
    template_id: int,
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    row = await get_template_by_id(session, template_id)
    if row is None:
        raise HTTPException(status_code=404, detail="template not found")
    return TemplateRead.model_validate(row)

@router.patch("/{template_id}", response_model=TemplateRead)
async def update_template_endpoint(
    template_id: int,
    payload: TemplateUpdate,
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    try:
        row = await update_template(session, template_id=template_id, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    
    if row is None:
        raise HTTPException(status_code=404, detail="template not found")
    return TemplateRead.model_validate(row)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template_endpoint(
    template_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    ok = await delete_template(session, template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="template not found")
    return None


@router.get("/resolve/latest", response_model=TemplateRead)
async def resolve_latest_template_endpoint(
    kind: TemplateKind = Query(...),
    name: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_session),
) -> TemplateRead:
    row = await get_latest_template_by_name(
        session,
        kind = kind,
        name = name,
    )
    if row is None:
        raise HTTPException(status_code=404, detail = "template not found")
    return TemplateRead.model_validate(row)