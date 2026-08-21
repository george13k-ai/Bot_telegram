from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, JSON
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.user import User


class EventType(str, enum.Enum):
    START = "START"
    SUBSCRIPTION_CHECK = "SUBSCRIPTION_CHECK"
    SUBSCRIBED = "SUBSCRIBED"
    INSTRUCTION_REQUESTED = "INSTRUCTION_REQUESTED"
    PDF_SENT = "PDF_SENT"
    FILE_UPLOADED = "FILE_UPLOADED"
    SPECIALIST_REQUESTED = "SPECIALIST_REQUESTED"
    MESSAGE_SENT = "MESSAGE_SENT"
    GIVEAWAY_OPENED = "GIVEAWAY_OPENED"
    GIVEAWAY_JOINED = "GIVEAWAY_JOINED"
    ADMIN_REPLY = "ADMIN_REPLY"


class UserEvent(TimestampMixin, Base):
    __tablename__ = "user_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[EventType] = mapped_column(SAEnum(EventType, name="event_type"), nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship(back_populates="events")
