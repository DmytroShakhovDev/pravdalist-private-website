"""Test: Path guard middleware and IP blocker."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.middleware.ip_blocker import IpBlockerMiddleware, MemoryIpStore
from app.middleware.path_guard import PathGuardMiddleware
from app.middleware.host_guard import HostGuardMiddleware
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.routers import api_v1, auth, pages


def _make_test_app(store: MemoryIpStore) -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(HostGuardMiddleware)
    test_app.add_middleware(PathGuardMiddleware)
    test_app.add_middleware(IpBlockerMiddleware, store=store)

    _static = Path(__file__).parent.parent / "app" / "static"
    test_app.mount("/static", StaticFiles(directory=str(_static)), name="static")
    test_app.include_router(api_v1.router)
    test_app.include_router(pages.router)
    test_app.include_router(auth.router)

    _tmpl = Jinja2Templates(directory=str(Path(__file__).parent.parent / "app" / "templates"))

    @test_app.exception_handler(404)
    async def not_found(request: Request, exc) -> HTMLResponse:
        request.state.violation_reason = f"not_found:{request.url.path}"
        return _tmpl.TemplateResponse(
            request, "errors/404.html", status_code=404
        )

    return test_app


@pytest.mark.asyncio
async def test_dotenv_returns_403():
    store = MemoryIpStore()
    app = _make_test_app(store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        r = await ac.get("/.env", headers={"host": "localhost"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unknown_route_returns_404_and_registers_violation():
    store = MemoryIpStore()
    app = _make_test_app(store)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        r = await ac.get("/totally-unknown", headers={"host": "localhost"})
    assert r.status_code == 404
    assert len(store._violations) >= 1


@pytest.mark.asyncio
async def test_ip_ban_after_threshold():
    """After exceeding violation threshold, subsequent requests return 403."""
    from app.config import get_settings
    from app.middleware.ip_blocker import _ban_cache
    settings = get_settings()
    store = MemoryIpStore()
    _ban_cache._cache.clear()
    app = _make_test_app(store)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        for _ in range(settings.ip_block_threshold + 1):
            await ac.get("/.env", headers={"host": "localhost"})

        r = await ac.get("/api/v1/health", headers={"host": "localhost"})

    assert r.status_code == 403
