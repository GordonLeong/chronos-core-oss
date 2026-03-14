from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from models import UniverseScanRequest, UniverseScanResponse, ScanRun, ScanStatus
from services.refresh_prices import refresh_universe_tickers
from services.candidate_engine import generate_candidates_for_template


async def run_universe_scan(
    session: AsyncSession,
    *,
    universe_id: int,
    req: UniverseScanRequest,
) -> UniverseScanResponse:
    
    # 1. Initialize Telemetry
    scan_run = ScanRun(
        universe_id=universe_id,
        template_id=req.template_id,
        status=ScanStatus.running,
    )
    session.add(scan_run)
    await session.commit()
    await session.refresh(scan_run)

    try:
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
        
        # 2. Record Metrics (Success)
        scan_run.status = ScanStatus.completed
        scan_run.tickers_processed = len(refresh_results)
        scan_run.ohlcv_rows_written = ohlcv_rows_written
        scan_run.candidates_created = candidates_created
        scan_run.error_count = error_count
        scan_run.ended_at = func.now()
        await session.commit()
        
        return UniverseScanResponse(
            scan_run_id=scan_run.id,
            universe_id=universe_id,
            template_id=req.template_id,
            tickers_processed=len(refresh_results),
            ohlcv_rows_written=ohlcv_rows_written,
            candidates_created=candidates_created,
            error_count=error_count,
        )
        
    except Exception as exc:
        # 3. Record Error (Failure)
        scan_run.status = ScanStatus.failed
        scan_run.error_text = str(exc)
        scan_run.ended_at = func.now()
        await session.commit()
        raise
