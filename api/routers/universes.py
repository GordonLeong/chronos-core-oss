from __future__ import annotations
from typing import Sequence, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from repositories.stocks import (
    get_or_create_stock,
    add_stock_to_universe,
    list_universe_stocks,
    remove_stock_from_universe,
    get_stock_by_ticker,
)

from ohlcv import list_ohlcv_rows
from services.ta.signals import list_signal_rows
import asyncio
from services.provider_registry import get_provider


from db import get_session
from models import UniverseCreate, UniverseRead, UniverseUpdate, CandidateRead, CandidateStatus
from repositories.universes import(
    create_universe,
    get_universe_by_id,
    list_universes,
    update_universe,
    delete_universe,
)

from repositories.candidates import list_candidates_for_universe

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


@router.get(
        "/{universe_id}/ohlcv",
            )

async def get_universe_ohlcv(
    universe_id: int,
    provider: str = Query("yahooquery"),
    interval: str = Query("1d"),
    limit: int | None = Query(None, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> dict:
    u = await get_universe_by_id(session, universe_id)
    if not u:
        raise HTTPException(status_code=404, detail="universe not found")
    
    stocks = await list_universe_stocks(session,universe_id=universe_id)

    data: dict[str, list[dict]] = {}
    for stock in stocks:
        rows = await list_ohlcv_rows(
            session, 
            stock_id=stock.id,
            provider=provider,
            interval=interval,
            limit=limit,
            order_desc=limit is not None,
        )
        data[stock.ticker]= [{
            "date": as_of.isoformat(),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
         for as_of, open_, high, low, close, volume in rows
        ]
    return{
        "universe_id": universe_id,
        "provider": provider,
        "interval": interval,
        "data": data,
    }

@router.get(
        "/{universe_id}/signals",
)
async def get_universe_signals(
    universe_id: int,
    provider: str = Query("yahooquery"),
    interval: str = Query("1d"),
    limit: int | None = Query(None, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),

) -> dict:
    u = await get_universe_by_id(session, universe_id)
    if not u:
        raise HTTPException(status_code=404, detail="universe not found")
    stocks = await list_universe_stocks(session, universe_id= universe_id)
    data: dict[str, list[dict]]={}
    for stock in stocks:
        rows = await list_signal_rows(
            session,
            stock_id=stock.id,
            provider=provider,
            interval=interval,
            limit=limit,
            order_desc=limit is not None,
        )
        data[stock.ticker] = [
            {
                "as_of": as_of.isoformat(),
                "rsi":rsi,
                "macd":macd,
                "macd_signal":macd_signal,
                "ema_20": ema_20,
                "ema_50": ema_50,
                "bb_upper": bb_upper,
                "bb_lower": bb_lower,

            }
            for (
                as_of,
                rsi,
                macd,
                macd_signal,
                ema_20,
                ema_50,
                bb_upper,
                bb_lower,

            ) in rows
        ]
    return {
        "universe_id": universe_id,
        "provider": provider,
        "interval": interval,
        "data":data,
    }

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

@router.get(
    "/{universe_id}/candidates",
    response_model=list[CandidateRead],
)
async def list_universe_candidates_endpoint(
    universe_id: int,
    status: CandidateStatus | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[CandidateRead]:
    u = await get_universe_by_id(session, universe_id)
    if not u:
        raise HTTPException(status_code=404, detail="universe not found")

    rows = await list_candidates_for_universe(
        session,
        universe_id=universe_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [CandidateRead.model_validate(r) for r in rows]


@router.post(
    "/{universe_id}/stocks",
    status_code=status.HTTP_201_CREATED,
)
async def add_ticker_to_universe_endpoint(
    universe_id: int,
    payload: AddTickerPayload,
    session: AsyncSession = Depends(get_session),
) -> dict:
    u = await get_universe_by_id(session, universe_id)
    if not u:
        raise HTTPException(status_code=404, detail="universe not found")
    
    ticker = payload.ticker.strip().upper()
    provider = get_provider("yahooquery")
    try:
        rows = await asyncio.to_thread(provider.fetch_ohlcv_rows, ticker, "1d")
    except Exception:
        rows = []
    if not rows:
        raise HTTPException(status_code=422, detail=f"invalid or unsupported ticker: {ticker}")
    
    stock = await get_or_create_stock(session, ticker, name=payload.name)
    link = await add_stock_to_universe(session, universe_id=universe_id, stock_id=stock.id)
    return { "universe_id" : link.universe_id, "stock_id": stock.id, "ticker": stock.ticker }

@router.patch(
    "/{universe_id}",
    response_model=UniverseRead,
)

async def update_universe_endpoint(
    universe_id: int,
    payload: UniverseUpdate,
    session: AsyncSession = Depends(get_session),
) -> UniverseRead:
    row = await update_universe(
        session,
        universe_id=universe_id,
        data=payload,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="universe not found")
    return UniverseRead.model_validate(row)