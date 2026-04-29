"""Database engine and session factory (async SQLAlchemy 2.x)."""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

_db_url = settings.database_url

_engine = create_async_engine(
    _db_url,
    echo=settings.app_env == "dev",
    pool_pre_ping=True,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    _engine, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def get_db_engine():
    return _engine
