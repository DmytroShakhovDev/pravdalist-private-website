"""Initial tables: users, ip_violations, ip_bans.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_superuser", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "ip_violations",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("ip", sa.String(45), index=True, nullable=False),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "ip_bans",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("ip", sa.String(45), unique=True, index=True, nullable=False),
        sa.Column("banned_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("ip_bans")
    op.drop_table("ip_violations")
    op.drop_table("users")
