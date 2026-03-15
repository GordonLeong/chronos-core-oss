from __future__ import annotations
from typing import Optional, Sequence

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Stock

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



