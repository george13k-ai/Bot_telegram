from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.user import User


class AudienceType(str, enum.Enum):
    ALL = "ALL"
    ACTIVATED = "ACTIVATED"
    TAG = "TAG"
    FILE_SENT = "FILE_SENT"


class MailingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    SENDING = "SENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class RecipientStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class Mailing(TimestampMixin, Base):
    __tablename__ = "mailings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    audience_type: Mapped[AudienceType] = mapped_column(SAEnum(AudienceType, name="audience_type"), nullable=False)
    audience_filter: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[MailingStatus] = mapped_column(
        SAEnum(MailingStatus, name="mailing_status"), default=MailingStatus.DRAFT, nullable=False
    )

    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)

    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blocked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    recipients: Mapped[list["MailingRecipient"]] = relationship(
        back_populates="mailing", cascade="all, delete-orphan"
    )


class MailingRecipient(Base):
    __tablename__ = "mailing_recipients"
    __table_args__ = (UniqueConstraint("mailing_id", "user_id", name="uq_mailing_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mailing_id: Mapped[int] = mapped_column(ForeignKey("mailings.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[RecipientStatus] = mapped_column(
        SAEnum(RecipientStatus, name="recipient_status"), default=RecipientStatus.PENDING, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    mailing: Mapped["Mailing"] = relationship(back_populates="recipients")
    user: Mapped["User"] = relationship(back_populates="mailing_recipients")
