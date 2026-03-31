import pytest
from httpx import AsyncClient, ASGITransport
import asyncio
from alembic.config import Config
from alembic import command
from main import app

def run_migrations():
    """Run alembic upgrade head synchronously to prepare the DB for testing."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

@pytest.mark.anyio
async def test_migrations_and_health():
    """Verify that applying migrations leads to a working API backend."""
    # Start fresh by ensuring the migrations compile and execute
    await asyncio.to_thread(run_migrations)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}
