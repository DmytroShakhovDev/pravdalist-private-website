"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.middleware.ip_blocker import MemoryIpStore


@pytest.fixture
def memory_store() -> MemoryIpStore:
    return MemoryIpStore()


@pytest.fixture
async def client(memory_store: MemoryIpStore):
    """Async test client with overridden IP store."""
    from fastapi import FastAPI, Request, status
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pathlib import Path

    from app.middleware.host_guard import HostGuardMiddleware
    from app.middleware.ip_blocker import IpBlockerMiddleware
    from app.middleware.path_guard import PathGuardMiddleware
    from app.routers import api_v1, auth, pages

    test_app = FastAPI()
    test_app.add_middleware(HostGuardMiddleware)
    test_app.add_middleware(PathGuardMiddleware)
    test_app.add_middleware(IpBlockerMiddleware, store=memory_store)

    _static_dir = Path(__file__).parent.parent / "app" / "static"
    test_app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

    test_app.include_router(pages.router)
    test_app.include_router(api_v1.router)
    test_app.include_router(auth.router)

    _templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "app" / "templates"))

    @test_app.exception_handler(404)
    async def not_found_handler(request: Request, exc) -> HTMLResponse:
        request.state.violation_reason = f"not_found:{request.url.path}"
        return _templates.TemplateResponse(
            request,
            "errors/404.html",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac, memory_store
