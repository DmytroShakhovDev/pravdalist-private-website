"""REST API v1 routes."""
from __future__ import annotations

from fastapi import APIRouter

from app.i18n.loader import load_page
from app.schemas.common import HealthResponse

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health-check endpoint."""
    return HealthResponse()


@router.get("/i18n/{page}/{lang}")
async def i18n_strings(page: str, lang: str) -> dict:
    """Return merged i18n strings for *page* + *lang* (used by Vue islands)."""
    return load_page(page, lang)
