from __future__ import annotations
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from sqlalchemy import select

from models import StrategyTemplate, TemplateCreate, TemplateKind, TemplateUpdate

async def create_template(
        session: AsyncSession,
        data: TemplateCreate,
) -> StrategyTemplate:
    row = StrategyTemplate(
        kind=data.kind,
        name=data.name,
        version = data.version,
        description = data.description,
        config_json = data.config_json,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("template kind/name/version already exists") from exc
    await session.refresh(row)
    return row


async def list_templates(
    session: AsyncSession,
    *,
    kind: Optional[TemplateKind] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[StrategyTemplate]:
    stmt = select(StrategyTemplate).order_by(
        StrategyTemplate.kind,
        StrategyTemplate.name,
        StrategyTemplate.version.desc()
    )
    if kind is not None:
      stmt = stmt.where(StrategyTemplate.kind == kind)
    
    stmt = stmt.limit(limit).offset(offset)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_template_by_id(
    session: AsyncSession,
    template_id: int,
) -> StrategyTemplate | None:
    return await session.get(StrategyTemplate, template_id)

async def delete_template(
    session: AsyncSession,
    template_id: int,
) -> bool:
    row = await session.get(StrategyTemplate, template_id)
    if row is None:
        return False
    await session.delete(row)
    await session.commit()
    return True


async def update_template(
    session: AsyncSession,
    *,
    template_id: int,
    data: TemplateUpdate,
) -> StrategyTemplate | None:
    row = await session.get(StrategyTemplate, template_id)
    if row is None:
        return None
    
    updates = data.model_dump(exclude_unset = True)
    for k, v in updates.items():
      setattr(row, k, v)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("template kind/name/version already exists") from exc
    await session.refresh(row)
    return row


async def get_latest_template_by_name(
    session: AsyncSession,
    *,
    kind: TemplateKind,
    name: str,
) -> StrategyTemplate | None:
    stmt = (
        select(StrategyTemplate)
        .where(
            StrategyTemplate.kind == kind,
            StrategyTemplate.name == name,
        )
        .order_by(StrategyTemplate.version.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()