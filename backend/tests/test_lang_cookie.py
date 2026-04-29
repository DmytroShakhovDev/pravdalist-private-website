"""Tests that language detection writes a Set-Cookie: lang=... header."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_lang_query_sets_cookie():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        r = await ac.get("/?lang=de", headers={"host": "localhost"})
    assert r.status_code == 200
    assert "lang=de" in r.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_lang_cookie_used_when_no_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        r = await ac.get("/", headers={"host": "localhost"}, cookies={"lang": "ru"})
    assert r.status_code == 200
    # The page should render with ru — check via html content or lang attribute
    assert "Правдалист" in r.text or 'lang="ru"' in r.text
