import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.anyio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}

@pytest.mark.anyio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/")
    assert res.status_code == 200
    assert "service" in res.json()
    assert res.json()["status"] == "ok"
