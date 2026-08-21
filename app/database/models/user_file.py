from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.support import SupportTicket
    from app.database.models.user import User


class UserFileStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    PROCESSED = "PROCESSED"


class UserFile(TimestampMixin, Base):
    __tablename__ = "user_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("support_tickets.id", ondelete="SET NULL"), nullable=True
    )

    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    status: Mapped[UserFileStatus] = mapped_column(
        SAEnum(UserFileStatus, name="user_file_status"), default=UserFileStatus.RECEIVED, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="files")
    ticket: Mapped["SupportTicket | None"] = relationship(back_populates="files")
