from __future__ import annotations
from datetime import date
from typing import Iterable, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import StockSignal


SignalRow = tuple[
    date,
    Optional[float],
    Optional[float],
    Optional[float],
    Optional[float],
    Optional[float],
    Optional[float],
    Optional[float],
]

async def upsert_signals(
    session: AsyncSession,
    *,
    stock_id: int,
    provider: str,
    interval: str,
    rows: Iterable[SignalRow],
) -> int:
    """
    Insert or update signal rows for one (stock, provider, interval).
    Returns the number of rows written or updated.
    """

    written = 0
    for (
        as_of,
        rsi,
        macd,
        macd_signal,
        ema_20,
        ema_50,
        bb_upper,
        bb_lower, 
    ) in rows:
        stmt = select(StockSignal).where(
            StockSignal.stock_id == stock_id,
            StockSignal.provider == provider,
            StockSignal.interval == interval,
            StockSignal.as_of == as_of,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            rec = StockSignal(
                stock_id=stock_id,
                as_of=as_of,
                provider=provider,
                interval=interval,
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                ema_20=ema_20,
                ema_50=ema_50,
                bb_upper=bb_upper,
                bb_lower=bb_lower,
            )
            session.add(rec)
        else:
            existing.rsi = rsi
            existing.macd = macd
            existing.macd_signal = macd_signal
            existing.ema_20 = ema_20
            existing.ema_50 = ema_50
            existing.bb_upper = bb_upper
            existing.bb_lower = bb_lower

        written += 1

    return written