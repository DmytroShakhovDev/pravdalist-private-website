"""IP blocker middleware — track violations and ban abusive IPs."""
from __future__ import annotations

import logging
import time
import uuid
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings
from app.db import async_session_factory

logger = logging.getLogger(__name__)
settings = get_settings()


class IpStore:
    """Abstract persistence for violations and bans."""

    async def add_violation(self, ip: str, path: str, reason: str) -> None: ...

    async def get_violation_count(self, ip: str, since: datetime) -> int: ...

    async def add_ban(self, ip: str, banned_until: datetime, reason: str) -> None: ...

    async def get_active_ban(self, ip: str) -> Optional[datetime]: ...


class DbIpStore(IpStore):
    """PostgreSQL-backed IpStore using async SQLAlchemy."""

    async def add_violation(self, ip: str, path: str, reason: str) -> None:
        try:
            async with async_session_factory() as session:
                await session.execute(
                    text(
                        "INSERT INTO ip_violations (ip, path, reason, created_at) "
                        "VALUES (:ip, :path, :reason, :ts)"
                    ),
                    {"ip": ip, "path": path, "reason": reason, "ts": datetime.now(UTC)},
                )
                await session.commit()
        except Exception:
            logger.debug("Could not record violation for %s", ip, exc_info=True)

    async def get_violation_count(self, ip: str, since: datetime) -> int:
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    text(
                        "SELECT COUNT(*) FROM ip_violations "
                        "WHERE ip = :ip AND created_at >= :since"
                    ),
                    {"ip": ip, "since": since},
                )
                return result.scalar_one()
        except Exception:
            logger.debug("Could not query violations for %s", ip, exc_info=True)
            return 0

    async def add_ban(self, ip: str, banned_until: datetime, reason: str) -> None:
        try:
            async with async_session_factory() as session:
                await session.execute(
                    text(
                        "INSERT INTO ip_bans (ip, banned_until, reason, created_at) "
                        "VALUES (:ip, :until, :reason, :ts) "
                        "ON CONFLICT (ip) DO UPDATE SET banned_until = EXCLUDED.banned_until, "
                        "reason = EXCLUDED.reason"
                    ),
                    {
                        "ip": ip,
                        "until": banned_until,
                        "reason": reason,
                        "ts": datetime.now(UTC),
                    },
                )
                await session.commit()
        except Exception:
            logger.debug("Could not insert ban for %s", ip, exc_info=True)

    async def get_active_ban(self, ip: str) -> Optional[datetime]:
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    text(
                        "SELECT banned_until FROM ip_bans "
                        "WHERE ip = :ip AND banned_until > :now"
                    ),
                    {"ip": ip, "now": datetime.now(UTC)},
                )
                row = result.fetchone()
                if row:
                    return row[0]
        except Exception:
            logger.debug("Could not query bans for %s", ip, exc_info=True)
        return None


class MemoryIpStore(IpStore):
    """In-memory IpStore for testing."""

    def __init__(self) -> None:
        self._violations: list[dict] = []
        self._bans: dict[str, datetime] = {}

    async def add_violation(self, ip: str, path: str, reason: str) -> None:
        self._violations.append({"ip": ip, "path": path, "reason": reason, "ts": datetime.now(UTC)})

    async def get_violation_count(self, ip: str, since: datetime) -> int:
        return sum(
            1 for v in self._violations if v["ip"] == ip and v["ts"] >= since
        )

    async def add_ban(self, ip: str, banned_until: datetime, reason: str) -> None:
        self._bans[ip] = banned_until

    async def get_active_ban(self, ip: str) -> Optional[datetime]:
        until = self._bans.get(ip)
        if until and until > datetime.now(UTC):
            return until
        return None


_BAN_CACHE_TTL = 30  # seconds


class _BanCache:
    """Simple in-memory LRU-like cache for active bans."""

    def __init__(self, ttl: float = _BAN_CACHE_TTL) -> None:
        self._cache: OrderedDict[str, tuple[Optional[datetime], float]] = OrderedDict()
        self._ttl = ttl

    def get(self, ip: str) -> tuple[bool, Optional[datetime]]:
        """Return (found_in_cache, banned_until_or_None)."""
        entry = self._cache.get(ip)
        if entry is None:
            return False, None
        ban_until, cached_at = entry
        if time.monotonic() - cached_at > self._ttl:
            del self._cache[ip]
            return False, None
        return True, ban_until

    def set(self, ip: str, ban_until: Optional[datetime]) -> None:
        if ip in self._cache:
            del self._cache[ip]
        self._cache[ip] = (ban_until, time.monotonic())
        if len(self._cache) > 10_000:
            self._cache.popitem(last=False)


_ban_cache = _BanCache()
_db_store = DbIpStore()


def _get_client_ip(request: Request) -> tuple[str, bool]:
    """
    Returns (ip, is_real).

    is_real=False signals the IP blocker to skip counting violations so that an
    unresolvable request never increments a shared counter or causes a global ban.
    """
    direct = request.client.host if request.client else None

    if settings.trust_proxy:
        # Optional: only honor the forwarded header when the immediate client
        # is in the configured trusted proxy list (prevents header spoofing).
        trusted = settings.trusted_proxy_ips_list
        if trusted and direct not in trusted:
            # Header may be spoofed — fall back to direct IP.
            return (direct or f"unresolved:{uuid.uuid4()}", direct is not None)

        forwarded = request.headers.get(settings.forwarded_header, "")
        if forwarded:
            # Take the left-most entry (closest to the real client).
            client_ip = forwarded.split(",")[0].strip()
            if client_ip:
                return (client_ip, True)

    if direct:
        return (direct, True)

    # No client information at all — generate a per-request placeholder so we
    # never share a violation bucket between unrelated unparseable requests.
    return (f"unresolved:{uuid.uuid4()}", False)


class IpBlockerMiddleware(BaseHTTPMiddleware):
    """
    Per-request:
      1. Check if IP is banned (cache -> DB).
      2. After response, record violation if flagged.
      3. If violation threshold exceeded, issue a ban.
    """

    def __init__(self, app, store: IpStore | None = None) -> None:
        super().__init__(app)
        self._store: IpStore = store or _db_store

    async def dispatch(self, request: Request, call_next) -> Response:
        ip, is_real = _get_client_ip(request)

        found, ban_until = _ban_cache.get(ip)
        if not found:
            ban_until = await self._store.get_active_ban(ip)
            _ban_cache.set(ip, ban_until)

        if ban_until and ban_until > datetime.now(UTC):
            return Response(
                content="Forbidden — IP temporarily banned",
                status_code=403,
                media_type="text/plain",
            )

        response: Response = await call_next(request)

        violation_reason: str | None = getattr(request.state, "violation_reason", None)
        # Only track violations when the IP is real, or when REQUIRE_REAL_CLIENT_IP
        # is False (permissive mode — always track).
        should_track = is_real or not settings.require_real_client_ip
        if (violation_reason or response.status_code in (403, 404)) and should_track:
            reason = violation_reason or f"http_{response.status_code}"
            path = request.url.path
            await self._handle_violation(ip, path, reason)

        return response

    async def _handle_violation(self, ip: str, path: str, reason: str) -> None:
        await self._store.add_violation(ip, path, reason)

        window_start = datetime.now(UTC) - timedelta(minutes=settings.ip_block_window_minutes)
        count = await self._store.get_violation_count(ip, window_start)

        if count >= settings.ip_block_threshold:
            ban_until = datetime.now(UTC) + timedelta(minutes=settings.ip_ban_minutes)
            await self._store.add_ban(ip, ban_until, f"threshold exceeded ({count} violations)")
            _ban_cache.set(ip, ban_until)
            logger.warning("Banned IP %s until %s (%d violations)", ip, ban_until, count)
