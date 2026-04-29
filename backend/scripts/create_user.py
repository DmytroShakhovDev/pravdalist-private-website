#!/usr/bin/env python3
"""Seed script: create a user in the database.

Usage:
    cd backend
    python scripts/create_user.py --email admin@example.com --password secret
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.db import async_session_factory, Base, get_db_engine
from app.models.user import User
from app.security import hash_password


async def create_user(email: str, password: str, superuser: bool = False) -> None:
    engine = await get_db_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"User {email} already exists.")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            is_superuser=superuser,
        )
        session.add(user)
        await session.commit()
        print(f"User {email} created (id={user.id}).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--superuser", action="store_true", default=False)
    args = parser.parse_args()
    asyncio.run(create_user(args.email, args.password, args.superuser))


if __name__ == "__main__":
    main()
