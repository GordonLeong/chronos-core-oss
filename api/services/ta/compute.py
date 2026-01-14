from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ohlcv import list_ohlcv_rows
from services.ta.signals import upsert_signals
from services.ta.registry import get_ta_provider


async def compute_and_upsert_signals(
        session: AsyncSession,
        *,
        stock_id: int,
        provider: str,
        interval: str,
        ta_provider: str = "pandas_ta",
) -> int:
    rows = await list_ohlcv_rows(
        session, stock_id=stock_id, provider=provider, interval=interval
    )
    if not rows:
        return 0

    impl = get_ta_provider(ta_provider)
    signal_rows = impl.compute_signals(rows)
    if not signal_rows:
        return 0

    return await upsert_signals(
        session,
        stock_id=stock_id,
        provider=provider,
        interval=interval,
        rows=signal_rows,
    )
