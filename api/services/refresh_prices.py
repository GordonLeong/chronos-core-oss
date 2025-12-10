# api/services/refresh_prices.py

from __future__ import annotations

from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from models import CacheStatus
from repositories.stocks import get_or_create_stock
from repositories.cache import upsert_cache_status
from ohlcv import upsert_ohlcv, OHLCVRow
from services.provider_registry import get_provider
from services.providers import yahooquery_adapter


class RefreshResult(TypedDict):
    ticker: str
    provider: str
    interval: str
    rows_written: int
    status: str
    detail: str | None


async def refresh_stock_prices(
    session: AsyncSession,
    *,
    ticker: str,
    provider: str,
    interval: str,
) -> RefreshResult:
    """
    Orchestrate a full refresh for one (ticker, provider, interval):

    1. Ensure Stock row exists.
    2. Mark cache as 'fetching'.
    3. Fetch OHLCV rows from provider.
    4. Upsert OHLCV rows into stock_ohlcv.
    5. Mark cache as 'fresh' (or 'error' on failure).

    Returns a small dict for API / logging.
    """

    # 1) ensure the Stock exists (idempotent)
    stock = await get_or_create_stock(session, ticker)

    # 2) mark cache as fetching
    await upsert_cache_status(
        session,
        stock_id=stock.id,
        provider=provider,
        interval=interval,
        status=CacheStatus.fetching,
        detail=None,
    )

    # 3 + 4) fetch from provider and upsert into DB
    rows_written = 0
    try:
        provider_impl = get_provider(provider)
        rows: list[OHLCVRow] = provider_impl.fetch_ohlcv_rows(stock.ticker, interval)
        rows_written = await upsert_ohlcv(
            session,
            stock_id=stock.id,
            provider=provider,
            interval=interval,
            rows=rows,
        )

        # 5) mark cache as fresh
        cache = await upsert_cache_status(
            session,
            stock_id=stock.id,
            provider=provider,
            interval=interval,
            status=CacheStatus.fresh,
            detail=None,
        )
        await session.commit()
    except Exception as exc:
        # on any failure, mark cache as error and re-raise
        cache = await upsert_cache_status(
            session,
            stock_id=stock.id,
            provider=provider,
            interval=interval,
            status=CacheStatus.error,
            detail=str(exc),
        )
        await session.commit()
        raise

    return RefreshResult(
        ticker=stock.ticker,
        provider=provider,
        interval=interval,
        rows_written=rows_written,
        status=cache.status.value if hasattr(cache.status, "value") else str(
            cache.status
        ),
        detail=cache.detail,
    )