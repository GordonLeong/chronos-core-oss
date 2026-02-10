from __future__ import annotations
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from sqlalchemy import select

from models import StrategyTemplate, TemplateCreate, TemplateKind

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