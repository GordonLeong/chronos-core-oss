# db.py
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncSession, async_sessionmaker,)
from sqlalchemy.orm import declarative_base

# SQLite file-based DB for phase 0.01. Change to postgres URL when ready.
DATABASE_URL = "sqlite+aiosqlite:///./chronos.db"

# Engine (async)
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Async session factory
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, 
    expire_on_commit=False,
    autoflush=False,
)



# Base model for ORM classes
Base = declarative_base()


async def init_db() -> None:
    """
    Create database tables from models.Base metadata.
    Run once at startup or during dev to create the sqlite file and tables.
    """
    async with engine.begin() as conn:
        # run_sync will execute the synchronous metadata.create_all in a threadpool
        await conn.run_sync(Base.metadata.create_all)
