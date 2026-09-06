"""add channel_join_requested_at to users

Revision ID: 0004_channel_join_request
Revises: 0003_update_alpha_bank_text
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0004_channel_join_request"
down_revision = "0003_update_alpha_bank_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("channel_join_requested_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "channel_join_requested_at")
