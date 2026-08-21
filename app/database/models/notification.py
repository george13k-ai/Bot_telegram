from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    NEW_USER = "NEW_USER"
    ACTIVATION = "ACTIVATION"
    NEW_PDF = "NEW_PDF"
    NEW_TICKET = "NEW_TICKET"
    NEW_MESSAGE = "NEW_MESSAGE"
    OTHER = "OTHER"


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType, name="notification_type"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_answered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
