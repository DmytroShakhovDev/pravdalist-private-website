"""Path guard middleware — block dangerous path patterns."""
from __future__ import annotations

import logging
import re
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.env(\b|$)", re.IGNORECASE),
    re.compile(r"\.git(/|$)", re.IGNORECASE),
    re.compile(r"\.bak(\b|$)", re.IGNORECASE),
    re.compile(r"\.sql(\b|$)", re.IGNORECASE),
    re.compile(r"\.php(\b|$)", re.IGNORECASE),
    re.compile(r"\.aspx(\b|$)", re.IGNORECASE),
    re.compile(r"wp-admin", re.IGNORECASE),
    re.compile(r"wp-login", re.IGNORECASE),
    re.compile(r"~$"),
    re.compile(r"\.swp$", re.IGNORECASE),
    re.compile(r"/\.well-known/(?!acme-challenge)", re.IGNORECASE),
]


def _is_blocked(path: str) -> bool:
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(path):
            return True
    return False


class PathGuardMiddleware(BaseHTTPMiddleware):
    """Block requests matching dangerous path patterns; record violations."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if _is_blocked(path):
            logger.warning("PathGuard blocked: %s", path)
            request.state.violation_reason = f"blocked_path:{path}"
            return Response(
                content="Forbidden",
                status_code=403,
                media_type="text/plain",
            )

        response: Response = await call_next(request)
        return response
