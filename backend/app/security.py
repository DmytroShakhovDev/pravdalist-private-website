"""JWT creation/verification and password hashing."""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return bcrypt hash of *plain* password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


def _build_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + expires_delta
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    """Create a short-lived access JWT."""
    return _build_token(
        {"sub": str(user_id), "type": "access"},
        timedelta(minutes=settings.jwt_access_ttl_min),
    )


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived refresh JWT."""
    return _build_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.jwt_refresh_ttl_days),
    )


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate an access JWT. Returns payload or None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        logger.debug("JWT verification failed")
        return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a refresh JWT. Returns payload or None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
