from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_session
from repositories.stocks import get_stock_by_ticker
from repositories.cache import get_cache_status
from models import CacheStatus

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