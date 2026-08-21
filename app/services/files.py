from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models.file import File, FilePurpose, FileType
from app.database.models.user_file import UserFile, UserFileStatus
from app.database.repositories.file_repo import FileRepository

ALLOWED_USER_DOCUMENT_MIME_TYPES = {"application/pdf"}


class FileValidationError(Exception):
    pass


class FileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FileRepository(session)

    def validate_user_document(self, mime_type: str | None, file_size: int | None) -> None:
        if mime_type not in ALLOWED_USER_DOCUMENT_MIME_TYPES:
            raise FileValidationError("Пожалуйста, отправьте файл в формате PDF.")
        if file_size is not None and file_size > settings.max_file_size_bytes:
            raise FileValidationError(
                f"Файл слишком большой. Максимальный размер — {settings.MAX_FILE_SIZE_MB} МБ."
            )

    async def save_user_document(
        self,
        user_id: int,
        telegram_file_id: str,
        file_name: str | None,
        mime_type: str | None,
        file_size: int | None,
        ticket_id: int | None = None,
    ) -> UserFile:
        return await self.repo.create_user_file(
            user_id=user_id,
            telegram_file_id=telegram_file_id,
            file_name=file_name,
            mime_type=mime_type,
            file_size=file_size,
            ticket_id=ticket_id,
        )

    async def mark_processed(self, user_file: UserFile) -> None:
        await self.repo.set_status(user_file, UserFileStatus.PROCESSED)

    async def get_content_file(self, purpose: FilePurpose) -> File | None:
        return await self.repo.get_by_purpose(purpose)

    async def set_content_file(
        self,
        purpose: FilePurpose,
        telegram_file_id: str,
        file_type: FileType,
        uploaded_by: int,
        file_name: str | None = None,
        mime_type: str | None = None,
        size: int | None = None,
    ) -> File:
        return await self.repo.upsert_content_file(
            purpose=purpose,
            telegram_file_id=telegram_file_id,
            file_type=file_type,
            uploaded_by=uploaded_by,
            file_name=file_name,
            mime_type=mime_type,
            size=size,
        )

    async def list_for_user(self, user_id: int) -> list[UserFile]:
        return await self.repo.list_for_user(user_id)
