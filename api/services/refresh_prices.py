# api/services/refresh_prices.py

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import TypedDict
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from db import AsyncSessionLocal
from models import CacheStatus
from repositories.cache import upsert_cache_status
from repositories.stocks import get_or_create_stock, list_active_tickers
from ohlcv import upsert_ohlcv, OHLCVRow
from services.provider_registry import get_provider


class RefreshResult(TypedDict):
    ticker: str
    provider: str
    interval: str
    rows_written: int
    status: str
    detail: str | None


logger = logging.getLogger("chronos.refresh_prices")
MARKET_TZ = ZoneInfo("America/New_York")
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)


def is_market_open(now: datetime | None = None) -> bool:
    """
    Hardcoded NYSE/Nasdaq hours (no holiday calendar yet).
    """
    if now is None:
        now = datetime.now(MARKET_TZ)
    now = now.astimezone(MARKET_TZ)
    if now.weekday() >= 5:
        return False
    current = now.time()
    return MARKET_OPEN <= current < MARKET_CLOSE


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
        rows: list[OHLCVRow] = await asyncio.to_thread(
            provider_impl.fetch_ohlcv_rows, stock.ticker, interval
        )
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


async def refresh_stock_prices_background(
    *,
    ticker: str,
    provider: str,
    interval: str,
) -> None:
    async with AsyncSessionLocal() as session:
        try:
            await refresh_stock_prices(
                session,
                ticker=ticker,
                provider=provider,
                interval=interval,
            )
        except Exception:
            logger.exception(
                "refresh failed (background)",
                extra={"ticker": ticker, "provider": provider, "interval": interval},
            )


async def refresh_active_tickers(
    *,
    provider: str = "yahooquery",
    interval: str = "1d",
) -> list[RefreshResult]:
    async with AsyncSessionLocal() as session:
        tickers = await list_active_tickers(session)
        if not tickers:
            logger.info("no active tickers to refresh")
            return []

        results: list[RefreshResult] = []
        for ticker in tickers:
            try:
                result = await refresh_stock_prices(
                    session,
                    ticker=ticker,
                    provider=provider,
                    interval=interval,
                )
                results.append(result)
            except Exception:
                logger.exception(
                    "refresh failed",
                    extra={"ticker": ticker, "provider": provider, "interval": interval},
                )
        return results


async def market_refresh_loop(
    *,
    stop_event: asyncio.Event,
    provider: str = "yahooquery",
    interval: str = "1d",
    refresh_every_seconds: int = 3600,
    off_hours_check_seconds: int = 900,
) -> None:
    """
    Refresh active tickers once per hour during market hours.
    """
    last_refresh: datetime | None = None
    logger.info("market refresh loop started")

    while not stop_event.is_set():
        now = datetime.now(MARKET_TZ)
        if is_market_open(now):
            should_refresh = (
                last_refresh is None
                or (now - last_refresh) >= timedelta(seconds=refresh_every_seconds)
            )
            if should_refresh:
                await refresh_active_tickers(provider=provider, interval=interval)
                last_refresh = now
            sleep_seconds = min(300, refresh_every_seconds)
        else:
            sleep_seconds = off_hours_check_seconds

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=sleep_seconds)
        except asyncio.TimeoutError:
            continue

    logger.info("market refresh loop stopped")
