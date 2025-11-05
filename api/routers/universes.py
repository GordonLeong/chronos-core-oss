from __future__ import annotations
from typing import Sequence, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from repositories.stocks import (
    get_or_create_stock,
    add_stock_to_universe,
    list_universe_stocks,
    remove_stock_from_universe,
    get_stock_by_ticker,
)


from db import get_session
from models import UniverseCreate, UniverseRead
from repositories.universes import(
    create_universe,
    get_universe_by_id,
    list_universes,
    delete_universe,
)


router = APIRouter(prefix="/universes", tags=["universes"])

class AddTickerPayload(BaseModel):
    ticker: str
    name: str | None = None

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


@router.post(
    "/{universe_id}/stocks",
    status_code = status.HTTP_201_CREATED,
)

async def add_ticker_to_universe_endpoint(
    universe_id: int,
    payload: AddTickerPayload,
    session: AsyncSession = Depends(get_session),
) -> dict:
    # ensure that the universe exists

    u = await get_universe_by_id(session, universe_id)
    if not u:
        raise HTTPException(status_code=404, detail="Universe not found")
    stock = await get_or_create_stock(session, payload.ticker, name=payload.name)
    link = await add_stock_to_universe(session, universe_id=universe_id, stock_id=stock.id)
    return {"universe_id": link.universe_id, "stock_id": stock.id, "ticker": stock.ticker}


@router.get(
    "/{universe_id}/stocks",
    response_model=list[str],
)
async def list_universe_stocks_endpoint(
    universe_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[str]:
    # 404 if universe missing
    u = await get_universe_by_id(session, universe_id)
    if not u:
        raise HTTPException(status_code=404, detail="universe not found")
    rows = await list_universe_stocks(session, universe_id=universe_id)
    return [ r.ticker for r in rows]

@router.delete(
    "/{universe_id}/stocks/{ticker}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_ticker_from_universe_endpoint(
    universe_id: int,
    ticker: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    #Optional: 404 if universe doesn't exist
    u = await get_universe_by_id(session, universe_id)
    if not u:
        raise HTTPException(status_code=404, detail="universe not found")
    
    stock = await get_or_create_stock(session, ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="stock not found")
    ok = await remove_stock_from_universe(
         session, universe_id=universe_id, stock_id=stock.id
   )
    if not ok:
        raise HTTPException(status_code=404, detail="membership not found")
    return None

