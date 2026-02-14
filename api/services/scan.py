from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession

from models import UniverseScanRequest, UniverseScanResponse
from services.refresh_prices import refresh_universe_tickers
from services.candidate_engine import generate_candidates_for_template


async def run_universe_scan(
    session: AsyncSession,
    *,
    universe_id: int,
    req: UniverseScanRequest,
) -> UniverseScanResponse:
    refresh_results = await refresh_universe_tickers(
        session,
        universe_id=universe_id,
        provider=req.provider,
        interval=req.interval,
    )
    ohlcv_rows_written = sum(r["rows_written"] for r in refresh_results)
    error_count = sum(1 for r in refresh_results if r["status"] == "error")
    candidates_created = await generate_candidates_for_template(
        session,
        universe_id=universe_id,
        template_id=req.template_id,
        provider=req.provider,
        interval=req.interval,
    )
    return UniverseScanResponse(
        universe_id=universe_id,
        template_id=req.template_id,
        tickers_processed=len(refresh_results),
        ohlcv_rows_written=ohlcv_rows_written,
        candidates_created=candidates_created,
        error_count=error_count,
     )
