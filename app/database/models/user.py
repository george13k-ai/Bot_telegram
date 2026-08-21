from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.giveaway import GiveawayParticipant
    from app.database.models.mailing import MailingRecipient
    from app.database.models.support import SupportTicket
    from app.database.models.tag import UserTag
    from app.database.models.user_event import UserEvent
    from app.database.models.user_file import UserFile


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    reminder_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tags: Mapped[list["UserTag"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    tickets: Mapped[list["SupportTicket"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    files: Mapped[list["UserFile"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    giveaway_participations: Mapped[list["GiveawayParticipant"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    events: Mapped[list["UserEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    mailing_recipients: Mapped[list["MailingRecipient"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def display_name(self) -> str:
        if self.username:
            return f"@{self.username}"
        name = " ".join(filter(None, [self.first_name, self.last_name]))
        return name or str(self.telegram_id)

    @property
    def mention_link(self) -> str:
        if self.username:
            return f"https://t.me/{self.username}"
        return f"tg://user?id={self.telegram_id}"
