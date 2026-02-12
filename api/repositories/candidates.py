from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import TradeCandidate, CandidateCreate, CandidateStatus


async def create_candidate(
    session: AsyncSession,
    data: CandidateCreate,
) -> TradeCandidate:
    row = TradeCandidate(
        universe_id=data.universe_id,
        template_id=data.template_id,
        ticker=data.ticker.upper().strip(),
        score=data.score,
        status=data.status,
        reason_code=data.reason_code,
        payload_json=data.payload_json,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row



async def list_candidates_for_universe(
    session: AsyncSession,
    *,
    universe_id: int,
    status: CandidateStatus | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[TradeCandidate]:
    stmt = select(TradeCandidate).where(
        TradeCandidate.universe_id == universe_id
    ).order_by(TradeCandidate.as_of.desc(), TradeCandidate.score.desc())

    if status is not None:
        stmt = stmt.where(TradeCandidate.status == status)

    stmt = stmt.limit(limit).offset(offset)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def update_candidate_status(
    session: AsyncSession,
    *,
    candidate_id: int,
    status: CandidateStatus,
    reason_code: str | None = None,
) -> TradeCandidate | None:
    row = await session.get(TradeCandidate, candidate_id)
    if row is None:
        return None
    row.status = status
    row.reason_code = reason_code
    await session.commit()
    await session.refresh(row)
    return row


async def create_candidates_bulk(
    session: AsyncSession,
    items: list[CandidateCreate],
) -> list[TradeCandidate]:
    if not items:
        return []

    rows: list[TradeCandidate] = []
    for data in items:
        row = TradeCandidate(
            universe_id=data.universe_id,
            template_id= data.template_id,
            ticker=data.ticker.upper().strip(),
            score=data.score,
            status=data.status,
            reason_code=data.reason_code,
            payload_json=data.payload_json,
        )
        session.add(row)
        rows.append(row)

    await session.commit()
    for row in rows:
        await session.refresh(row)
    return rows