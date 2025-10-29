from __future__ import annotations
from typing import Sequence, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


from db import AsyncSessionLocal
from models import UniverseCreate, UniverseRead
from repositories.universes import(
    create_universe,
    get_universe_by_id,
    list_universes,
    delete_universe,
)


router = APIRouter(prefix="/universes", tags=["universes"])

#--- session dependency

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

@router.post(
    "",
    response_model=UniverseRead,
    status_code= status.HTTP_201_CREATED,
)

async def create_universe_endpoint(
    payload: UniverseCreate,
    session: AsyncSession = Depends(get_session),

) -> UniverseRead:
    u = await create_universe(session, payload)
    return UniverseRead.model_validate(u)


# GET /universes/{id}
@router.get(
    "/{universe_id}",
    response_model=UniverseRead,
)
async def get_universe_endpoint(
    universe_id: int,
    session: AsyncSession = Depends(get_session),
) -> UniverseRead:
    u = await get_universe_by_id(session, universe_id)
    if not u:
        raise HTTPException(status_code=404, detail="universe not found")
    return UniverseRead.model_validate(u)

# GET /universes
@router.get(
    "",
    response_model=list[UniverseRead],
)
async def list_universes_endpoint(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> Sequence[UniverseRead]:
    rows = await list_universes(session, limit=limit, offset=offset)
    return [UniverseRead.model_validate(r) for r in rows]

# DELETE /universes/{id}
@router.delete(
    "/{universe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_universe_endpoint(
    universe_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    ok = await delete_universe(session, universe_id)
    if not ok:
        raise HTTPException(status_code=404, detail="universe not found")
    return None