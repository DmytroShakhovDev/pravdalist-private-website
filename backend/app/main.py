"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.middleware.host_guard import HostGuardMiddleware
from app.middleware.ip_blocker import IpBlockerMiddleware
from app.middleware.path_guard import PathGuardMiddleware
from app.routers import api_v1, auth, pages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Pravdalist Private",
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env == "dev" else None,
    redoc_url=None,
)

app.add_middleware(HostGuardMiddleware)
app.add_middleware(PathGuardMiddleware)
app.add_middleware(IpBlockerMiddleware)

_static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

app.include_router(pages.router)
app.include_router(api_v1.router)
app.include_router(auth.router)

_templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.exception_handler(404)
async def not_found_handler(request: Request, exc) -> HTMLResponse:
    request.state.violation_reason = f"not_found:{request.url.path}"
    return _templates.TemplateResponse(
        request,
        "errors/404.html",
        status_code=status.HTTP_404_NOT_FOUND,
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc) -> HTMLResponse:
    return _templates.TemplateResponse(
        request,
        "errors/403.html",
        status_code=status.HTTP_403_FORBIDDEN,
    )


@app.exception_handler(429)
async def too_many_requests_handler(request: Request, exc) -> HTMLResponse:
    return _templates.TemplateResponse(
        request,
        "errors/429.html",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )
