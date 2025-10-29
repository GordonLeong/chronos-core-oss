# db.py
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncSession, async_sessionmaker,)
from sqlalchemy.orm import DeclarativeBase
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

# SQLite file-based DB for phase 0.01. Change to postgres URL when ready.
DATABASE_URL = "sqlite+aiosqlite:///./chronos.db"

# Engine (async)
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Base model for ORM classes
class Base(DeclarativeBase):
    pass

# Async session factory
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, 
    expire_on_commit=False,
    autoflush=False,
)

try: 
    import models
except Exception:
    logging.getLogger(__name__).exception("Failed to import")

async def init_db() -> None:
    """
    Create database tables from models.Base metadata.
    Run once at startup or during dev to create the sqlite file and tables.
    """
    async with engine.begin() as conn:
        # run_sync will execute the synchronous metadata.create_all in a threadpool
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

        