from __future__ import annotations
from typing import Optional, Sequence
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


from models import Universe, UniverseCreate

async def create_universe(session: AsyncSession, data: UniverseCreate) -> Universe:
    """
    Insert a new Universe, raise ValueError if name already exists
    
    """
    u = Universe(name=data.name, description=data.description)
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u

async def get_universe_by_id(session: AsyncSession, universe_id: int) -> Optional[Universe]:
    res = await session.execute(select(Universe).where(Universe.id == universe_id))
    return res.scalar_one_or_none()


async def list_universes(
        session: AsyncSession, *, limit: int = 50, offset: int = 0
) -> Sequence[Universe]:
    res = await session.execute(
        select(Universe).order_by(Universe.id).limit(limit).offset(offset)
    )

    return res.scalars().all()


async def delete_universe(session: AsyncSession, universe_id: int) -> bool:
    """
    Load and delete to avoid relying on .rowcount
    Returns True if an entity existed and was deleted.
    """
    obj = await session.get(Universe, universe_id)
    if obj is None:
        return False
    await session.delete(obj)
    await session.commit()
    return True