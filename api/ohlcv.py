from __future__ import annotations
from datetime import date
from typing import Iterable, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import StockOHLCV


OHLCVRow = tuple[date, float, float, float, float, Optional[float]]

async def upsert_ohlcv(
        session: AsyncSession,
        *,
        stock_id: int,
        provider: str,
        interval: str,
        rows: Iterable[OHLCVRow],
) -> int:
    """
    Insert or update OHLCV rows for one (stock, provider, interval).
    Returns the number of rows written or updated.
    """

    written = 0

    for as_of, open_, high, low, close, volume in rows:
        stmt = select(StockOHLCV).where(
            StockOHLCV.stock_id == stock_id,
            StockOHLCV.provider == provider,
            StockOHLCV.interval == interval,
            StockOHLCV.as_of == as_of,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            rec = StockOHLCV(
                stock_id =stock_id,
                as_of = as_of,
                provider = provider,
                interval = interval,
                open = open_,
                high = high,
                low = low,
                close = close,
                volume = volume,

            )
            session.add(rec)
        else:
            existing.open = open_
            existing.high = high
            existing.low = low
            existing.close = close
            existing.volume = volume
        written += 1

    return written


async def list_ohlcv_rows(
    session: AsyncSession,
    *,
    stock_id: int,
    provider: str,
    interval: str,
    limit: int | None = None,

) -> list[OHLCVRow]:
    """
 Read OHLCV Rows for one(stock, provider,interval).
    """
    stmt = select(StockOHLCV).where(
        StockOHLCV.stock_id == stock_id,
        StockOHLCV.provider == provider,
        StockOHLCV.interval == interval,
    ).order_by(StockOHLCV.as_of)

    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    rows = []
    for rec in result.scalars().all():
        rows.append((rec.as_of, rec.open, rec.high, rec.low, rec.close, rec.volume))
    return rows