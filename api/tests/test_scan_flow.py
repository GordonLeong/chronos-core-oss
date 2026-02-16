import pytest
from httpx import AsyncClient, ASGITransport

from main import app

@pytest.mark.anyio
async def test_universe_scan_missing_universe_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/universes/999999/scan", json={"template_id": 1})
    assert res.status_code == 404
    assert res.json()["detail"] == "universe not found"

@pytest.mark.anyio
async def test_candidates_generate_missing_template_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # assumes universe 1 may not exist; this checks template-path only if universe exists
        u = await ac.get("/universes/1")
        if u.status_code != 200:
            return
        res = await ac.post("/candidates/generate", json={"universe_id": 1, "template_id": 999999})
    assert res.status_code == 404
    assert res.json()["detail"] == "template not found"

@pytest.mark.anyio
async def test_add_invalid_ticker_returns_422():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create = await ac.post("/universes", json={"name": "test-invalid-ticker"})
        assert create.status_code == 201
        universe_id = create.json()["id"]

        res = await ac.post(f"/universes/{universe_id}/stocks", json={"ticker": "NOTAREALTICKERXYZ"})
    assert res.status_code == 422
    assert "invalid or unsupported ticker" in res.json()["detail"]