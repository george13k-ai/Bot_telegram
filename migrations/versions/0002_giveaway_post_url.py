"""add post_url to giveaways

Revision ID: 0002_giveaway_post_url
Revises: 0001_initial
Create Date: 2026-08-31
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002_giveaway_post_url"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("giveaways", sa.Column("post_url", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("giveaways", "post_url")
