"""Test: Host guard middleware."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_bad_host_returns_421():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://evil.example.com") as ac:
        response = await ac.get("/api/v1/health", headers={"host": "evil.example.com"})
    assert response.status_code == 421


@pytest.mark.asyncio
async def test_allowed_host_passes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        response = await ac.get("/api/v1/health", headers={"host": "localhost"})
    assert response.status_code == 200
