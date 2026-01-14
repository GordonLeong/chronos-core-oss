import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from repositories.stocks import get_stock_by_ticker
from repositories.cache import get_cache_status, upsert_cache_status
from models import CacheStatus
from ohlcv import list_ohlcv_rows
from services.ta.signals import list_signal_rows
from services.refresh_prices import refresh_stock_prices_background

router = APIRouter(prefix="/stocks", tags =["stocks"])

@router.get("/{ticker}/status")
async def get_stock_status(
    ticker: str,
    provider: str = Query("yahooquery"),
    interval: str = Query("1d"),
    session: AsyncSession = Depends(get_session),

) -> dict:
    stock = await get_stock_by_ticker(session, ticker)
    if not stock:
        raise HTTPException(status_code=404, detail ="stock not found")
    row = await get_cache_status(session, stock_id = stock.id, provider=provider, interval=interval)
    if not row:
        return{
            "ticker": stock.ticker, "provider": provider, "interval": interval, "status": CacheStatus.unknown.value
        }
    return {
        "ticker": stock.ticker,
        "provider": row.provider,
        "interval": row.interval,
        "status": row.status.value,
        "last_fetched_at": row.last_fetched_at.isoformat() if row.last_fetched_at else None,
        "detail": row.detail

    }

@router.get("/{ticker}/ohlcv")
async def get_stock_ohlcv(
    ticker: str,
    provider: str = Query("yahooquery"),
    interval: str = Query("1d"),
    limit: int | None = Query(None, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    stock = await get_stock_by_ticker(session, ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="stock not found")

    rows = await list_ohlcv_rows(
        session,
        stock_id=stock.id,
        provider=provider,
        interval=interval,
        limit=limit,
        order_desc=limit is not None,
    )

    return [
        {
            "date": as_of.isoformat(),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
        for as_of, open_, high, low, close, volume in rows
    ]


@router.get("/{ticker}/signals")
async def get_stock_signals(
    ticker: str,
    provider: str = Query("yahooquery"),
    interval: str = Query("1d"),
    limit: int | None = Query(None, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    stock = await get_stock_by_ticker(session, ticker)
    if not stock:
        raise HTTPException(status_code=404, detail="stock not found")

    rows = await list_signal_rows(
        session,
        stock_id=stock.id,
        provider=provider,
        interval=interval,
        limit=limit,
        order_desc=limit is not None,
    )

    return [
        {
            "as_of": as_of.isoformat(),
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
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


@router.post("/{ticker}/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh_stock(
    ticker: str,
    provider: str = Query("yahooquery"),
    interval: str = Query("1d"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    #resolve ticker -> stock:
    stock = await get_stock_by_ticker(session, ticker)
    if not stock:
        raise HTTPException(status_code=404, detail = "stock not found")
    
    await upsert_cache_status(
        session,
        stock_id = stock.id,
        provider = provider,
        interval = interval,
        status = CacheStatus.fetching,
        detail = "refresh scheduled"
    )

    asyncio.create_task(
        refresh_stock_prices_background(
            ticker=stock.ticker,
            provider=provider,
            interval=interval,
        )
    )

    row = await get_cache_status(
        session, stock_id=stock.id, provider=provider, interval=interval
    )


    return {
        "ticker": stock.ticker,
        "provider": provider,
        "interval": interval,
        "status": row.status.value if row else CacheStatus.fetching.value,
        "last_fetched_at": row.last_fetched_at.isoformat() if row and row.last_fetched_at else None,
        "detail": row.detail if row else "refresh scheduled",
    }
    
