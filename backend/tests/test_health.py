"""Test: GET /api/v1/health returns 200."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        response = await ac.get("/api/v1/health", headers={"host": "localhost"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
