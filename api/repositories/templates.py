from __future__ import annotations
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import StrategyTemplate, TemplateCreate

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
