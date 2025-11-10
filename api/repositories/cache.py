from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Stock, StockPriceCache, CacheStatus



async def get_cache_status(
    session: AsyncSession, *, stock_id: int, provider: str, interval: str
) -> Optional[StockPriceCache]:
    
    """
    Returns the cache row for stock, provider, interval , if it exists
    """

    res = await session.execute(
        select(StockPriceCache).where(
            StockPriceCache.stock_id == stock_id,
            StockPriceCache.provider == provider,
            StockPriceCache.interval == interval,
        )
    )

    return res.scalar_one_or_none()

async def upsert_cache_status(
    session: AsyncSession,
    *,
    stock_id: int,
    provider: str,
    interval: str,
    status: CacheStatus,
    detail: Optional[str] = None,

) -> StockPriceCache:
    """
    Insert or update cache status for a stock.
    """
    row = await get_cache_status(
        session, stock_id = stock_id, provider=provider, interval=interval
    )

    now = datetime.now(timezone.utc)

    if row:
        row.status = status
        row.last_fetched_at = now
        row.detail = detail
    else:
        row = StockPriceCache(
            stock_id = stock_id,
            provider = provider,
            interval = interval,
            status = status,
            last_fetched_at = now,
            detail = detail
        )
        session.add(row)

    await session.commit()
    await session.refresh(row)

    return row


