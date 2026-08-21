"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-17
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_subscribed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("reminder_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reminder_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_admins_telegram_id", "admins", ["telegram_id"], unique=True)

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "content",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("media_type", sa.String(50), nullable=True),
        sa.Column("media_file_id", sa.String(255), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
    )

    op.create_table(
        "files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_file_id", sa.String(255), nullable=False),
        sa.Column(
            "file_type",
            sa.Enum("PHOTO", "DOCUMENT", "VIDEO", name="file_type"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size", sa.BigInteger(), nullable=True),
        sa.Column(
            "purpose",
            sa.Enum(
                "ALPHA_BANK_IMAGE",
                "INSTRUCTION_PDF",
                "USER_DOCUMENT",
                "GIVEAWAY_IMAGE",
                "MAILING_IMAGE",
                name="file_purpose",
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column("uploaded_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "giveaways",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_file_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "mailings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("photo_file_id", sa.String(255), nullable=True),
        sa.Column(
            "audience_type",
            sa.Enum("ALL", "ACTIVATED", "TAG", "FILE_SENT", name="audience_type"),
            nullable=False,
        ),
        sa.Column("audience_filter", sa.JSON(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT", "SCHEDULED", "SENDING", "COMPLETED", "CANCELLED", "FAILED", name="mailing_status"
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "user_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "tag_id", name="uq_user_tag"),
    )

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "NEW",
                "WAITING_FOR_FILE",
                "FILE_RECEIVED",
                "WAITING_FOR_ADMIN",
                "ANSWERED",
                "CLOSED",
                name="ticket_status",
            ),
            nullable=False,
            server_default="NEW",
        ),
        sa.Column(
            "source",
            sa.Enum("SPECIALIST_REQUEST", "PDF_UPLOAD", "MESSAGE", name="ticket_source"),
            nullable=False,
        ),
        sa.Column("calculated_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("reminder_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reminder_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "giveaway_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "giveaway_id", sa.Integer(), sa.ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("giveaway_id", "user_id", name="uq_giveaway_user"),
    )

    op.create_table(
        "mailing_recipients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mailing_id", sa.Integer(), sa.ForeignKey("mailings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SENT", "FAILED", "BLOCKED", name="recipient_status"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("mailing_id", "user_id", name="uq_mailing_user"),
    )

    op.create_table(
        "support_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "ticket_id",
            sa.Integer(),
            sa.ForeignKey("support_tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender", sa.Enum("USER", "ADMIN", name="message_sender"), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "ANSWERED", name="message_status"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "user_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "ticket_id",
            sa.Integer(),
            sa.ForeignKey("support_tickets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("telegram_file_id", sa.String(255), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("RECEIVED", "PROCESSED", name="user_file_status"),
            nullable=False,
            server_default="RECEIVED",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "type",
            sa.Enum(
                "NEW_USER",
                "ACTIVATION",
                "NEW_PDF",
                "NEW_TICKET",
                "NEW_MESSAGE",
                "OTHER",
                name="notification_type",
            ),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column(
            "ticket_id",
            sa.Integer(),
            sa.ForeignKey("support_tickets.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_answered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("admin_id", sa.BigInteger(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "user_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "START",
                "SUBSCRIPTION_CHECK",
                "SUBSCRIBED",
                "INSTRUCTION_REQUESTED",
                "PDF_SENT",
                "FILE_UPLOADED",
                "SPECIALIST_REQUESTED",
                "MESSAGE_SENT",
                "GIVEAWAY_OPENED",
                "GIVEAWAY_JOINED",
                "ADMIN_REPLY",
                name="event_type",
            ),
            nullable=False,
        ),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_events")
    op.drop_table("notifications")
    op.drop_table("user_files")
    op.drop_table("support_messages")
    op.drop_table("mailing_recipients")
    op.drop_table("giveaway_participants")
    op.drop_table("support_tickets")
    op.drop_table("user_tags")
    op.drop_table("mailings")
    op.drop_table("giveaways")
    op.drop_table("files")
    op.drop_table("content")
    op.drop_table("tags")
    op.drop_table("admins")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_name in (
        "event_type",
        "notification_type",
        "user_file_status",
        "message_status",
        "message_sender",
        "recipient_status",
        "ticket_source",
        "ticket_status",
        "mailing_status",
        "audience_type",
        "file_purpose",
        "file_type",
    ):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
