import logging
import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db import AsyncSessionLocal
from models import CacheStatus
from repositories.stocks import get_stock_by_ticker
from repositories.cache import upsert_cache_status
from ohlcv import upsert_ohlcv
from services.ta.compute import compute_and_upsert_signals
from services.provider_registry import get_provider

logger = logging.getLogger("chronos.refresh")

async def refresh_stock_prices(
    session: AsyncSession,
    *,
    stock_id: int,
    ticker: str,
    provider: str,
    interval: str,
) -> None:
    """Fetch OHLCV, compute TA, and update cache status for a single stock."""
    impl = get_provider(provider)
    
    try:
        # We fetch via provider and then upsert
        # Note: the provider registry in this project returns an integer count from fetch_ohlcv
        # but the rows are inserted by the provider in the background into ohlcv.
        # Looking at provider_registry.py interface, fetch_ohlcv returns int. Let's look closer.
        # Actually fetch_ohlcv_rows returns list[OHLCVRow].
        rows = impl.fetch_ohlcv_rows(ticker=ticker, interval=interval)
        
        if rows:
            await upsert_ohlcv(
                session,
                stock_id=stock_id,
                provider=provider,
                interval=interval,
                rows=rows,
            )
            # Compute indicators
            await compute_and_upsert_signals(
                session,
                stock_id=stock_id,
                provider=provider,
                interval=interval,
            )
            
        await upsert_cache_status(
            session,
            stock_id=stock_id,
            provider=provider,
            interval=interval,
            status=CacheStatus.fresh,
            detail=f"Refreshed {len(rows)} rows",
        )
    except Exception as exc:
        logger.exception("Failed to refresh stock %s: %s", ticker, exc)
        await upsert_cache_status(
            session,
            stock_id=stock_id,
            provider=provider,
            interval=interval,
            status=CacheStatus.error,
            detail=str(exc),
        )

async def refresh_stock_prices_background(
    ticker: str, provider: str, interval: str
) -> None:
    """Entrypoint for background refresh of a single stock."""
    try:
        async with AsyncSessionLocal() as session:
            stock = await get_stock_by_ticker(session, ticker)
            if not stock:
                logger.warning("Stock %s not found, skipping background refresh", ticker)
                return
            await refresh_stock_prices(
                session,
                stock_id=stock.id,
                ticker=ticker,
                provider=provider,
                interval=interval,
            )
    except Exception as exc:
        logger.exception("Background refresh task failed for %s", ticker)
