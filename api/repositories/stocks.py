from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Stock, UniverseMember

#  // normalize the ticker to uppercase
def _norm_ticker(t: str) -> str:
    return t.strip().upper()

async def get_stock_by_ticker(session: AsyncSession, ticker: str) -> Optional[Stock]:
    """
    Fetch a stock by normalised ticker. Returns None if not found
    """
    T = _norm_ticker(ticker)
    res = await session.execute(select(Stock).where(Stock.ticker==T))
    return res.scalar_one_or_none()

async def get_or_create_stock(
        session: AsyncSession, ticker: str, name: Optional[str] = None 
) -> Stock:
    
    """
    Idempotent: returns existing row if ticker exists; else creates it.
    Safe under concurrent inserts via unique constraint on Stock.ticker.
    """

    T = _norm_ticker(ticker)
    res = await session.execute(select(Stock).where(Stock.ticker == T))
    row = res.scalar_one_or_none()
    if row:
        return row
    
    s = Stock(ticker=T, name=name)
    session.add(s)
    try:
        await session.commit()
    except IntegrityError:
        #Another transaction inserted the smae ticker, so fetch it instead

        await session.rollback()
        res = await session.execute(select(Stock).where(Stock.ticker == T))
        return res.scalar_one()
    
    await session.refresh(s)
    return s


async def add_stock_to_universe(
        session: AsyncSession, *, universe_id: int, stock_id: int
) -> UniverseMember:
    """
    Create the universe, stock, link if it doesn't exist. Idempotent.
    """

    res = await session.execute(select(UniverseMember).where(
        UniverseMember.universe_id == universe_id,
        UniverseMember.stock_id == stock_id,
        )
    )

    link = res.scalar_one_or_none()
    if link:
        return link
    
    link = UniverseMember(universe_id = universe_id, stock_id = stock_id)
    session.add(link)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        res = await session.execute(
            select(UniverseMember).where(
                UniverseMember.universe_id == universe_id,
                UniverseMember.stock_id == stock_id
            )
        )
        return res.scalar_one()
    await session.refresh(link)
    return link

async def list_universe_stocks(
        session: AsyncSession, * , universe_id: int
) -> Sequence[Stock]:
    
    """
    Return all stock rows linked to a universe
    """
    res = await session.execute(
        select(UniverseMember.stock_id). where(UniverseMember.universe_id == universe_id)
    )
    stock_ids = [sid for (sid, ) in res.all()]
    if not stock_ids:
        return []
    
    res2 = await session.execute(
        select(Stock).where(Stock.id.in_(stock_ids)).order_by(Stock.ticker)
    )
    return res2.scalars().all()


async def list_active_tickers(session: AsyncSession) -> list[str]:
    """
    Return distinct tickers that appear in at least one universe.
    """
    res = await session.execute(
        select(Stock.ticker)
        .join(UniverseMember, UniverseMember.stock_id == Stock.id)
        .distinct()
        .order_by(Stock.ticker)
    )
    return [row[0] for row in res.all()]


async def remove_stock_from_universe(
    session: AsyncSession, *, universe_id: int, stock_id: int
) -> bool:
    
    """
    Delete the (universe, stock) membership. Returns True if a link existed.
    """
    res = await session.execute(
        delete(UniverseMember).where(
            UniverseMember.universe_id == universe_id,
            UniverseMember.stock_id == stock_id,
        )
    )

    await session.commit()
    return bool(getattr(res, "rowcount", 0))
