"""Host guard middleware — allows only configured hostnames."""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HostGuardMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Host header is not in ALLOWED_HOSTS."""

    async def dispatch(self, request: Request, call_next) -> Response:
        host = request.headers.get("host", "").split(":")[0]  # strip port
        if host not in settings.allowed_hosts_list:
            logger.warning("Blocked request with Host=%s", host)
            return Response(
                content="Misdirected Request",
                status_code=421,
                media_type="text/plain",
            )
        return await call_next(request)
