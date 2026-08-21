from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.user import User
    from app.database.models.user_file import UserFile


class TicketStatus(str, enum.Enum):
    NEW = "NEW"
    WAITING_FOR_FILE = "WAITING_FOR_FILE"
    FILE_RECEIVED = "FILE_RECEIVED"
    WAITING_FOR_ADMIN = "WAITING_FOR_ADMIN"
    ANSWERED = "ANSWERED"
    CLOSED = "CLOSED"


TICKET_STATUS_LABELS = {
    TicketStatus.NEW: "Новая",
    TicketStatus.WAITING_FOR_FILE: "Ожидает файл",
    TicketStatus.FILE_RECEIVED: "Файл получен",
    TicketStatus.WAITING_FOR_ADMIN: "Ожидает ответа",
    TicketStatus.ANSWERED: "Отвечено",
    TicketStatus.CLOSED: "Завершена",
}


class TicketSource(str, enum.Enum):
    SPECIALIST_REQUEST = "SPECIALIST_REQUEST"
    PDF_UPLOAD = "PDF_UPLOAD"
    MESSAGE = "MESSAGE"


class MessageSender(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class MessageStatus(str, enum.Enum):
    PENDING = "PENDING"
    ANSWERED = "ANSWERED"


class SupportTicket(TimestampMixin, Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        SAEnum(TicketStatus, name="ticket_status"), default=TicketStatus.NEW, nullable=False
    )
    source: Mapped[TicketSource] = mapped_column(SAEnum(TicketSource, name="ticket_source"), nullable=False)
    calculated_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    reminder_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reminder_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="tickets")
    messages: Mapped[list["SupportMessage"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="SupportMessage.created_at"
    )
    files: Mapped[list["UserFile"]] = relationship(back_populates="ticket")

    @property
    def status_label(self) -> str:
        return TICKET_STATUS_LABELS.get(self.status, self.status.value)


class SupportMessage(TimestampMixin, Base):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    sender: Mapped[MessageSender] = mapped_column(SAEnum(MessageSender, name="message_sender"), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MessageStatus] = mapped_column(
        SAEnum(MessageStatus, name="message_status"), default=MessageStatus.PENDING, nullable=False
    )

    ticket: Mapped["SupportTicket"] = relationship(back_populates="messages")
