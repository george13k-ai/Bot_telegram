from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class FileType(str, enum.Enum):
    PHOTO = "PHOTO"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"


class FilePurpose(str, enum.Enum):
    ALPHA_BANK_IMAGE = "ALPHA_BANK_IMAGE"
    INSTRUCTION_PDF = "INSTRUCTION_PDF"
    USER_DOCUMENT = "USER_DOCUMENT"
    GIVEAWAY_IMAGE = "GIVEAWAY_IMAGE"
    MAILING_IMAGE = "MAILING_IMAGE"


class File(TimestampMixin, Base):
    """Centralized registry of bot-managed content media (not user uploads)."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(SAEnum(FileType, name="file_type"), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    purpose: Mapped[FilePurpose] = mapped_column(
        SAEnum(FilePurpose, name="file_purpose"), nullable=False, unique=True
    )
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
