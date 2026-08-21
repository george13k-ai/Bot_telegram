from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.file import File, FilePurpose, FileType
from app.database.models.user_file import UserFile, UserFileStatus


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- centralized content media (app.database.models.file.File) ---

    async def get_by_purpose(self, purpose: FilePurpose) -> File | None:
        result = await self.session.execute(select(File).where(File.purpose == purpose))
        return result.scalar_one_or_none()

    async def upsert_content_file(
        self,
        purpose: FilePurpose,
        telegram_file_id: str,
        file_type: FileType,
        uploaded_by: int | None,
        file_name: str | None = None,
        mime_type: str | None = None,
        size: int | None = None,
    ) -> File:
        existing = await self.get_by_purpose(purpose)
        if existing is not None:
            existing.telegram_file_id = telegram_file_id
            existing.file_type = file_type
            existing.uploaded_by = uploaded_by
            existing.file_name = file_name
            existing.mime_type = mime_type
            existing.size = size
            await self.session.flush()
            return existing
        record = File(
            purpose=purpose,
            telegram_file_id=telegram_file_id,
            file_type=file_type,
            uploaded_by=uploaded_by,
            file_name=file_name,
            mime_type=mime_type,
            size=size,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    # --- user-uploaded files (app.database.models.user_file.UserFile) ---

    async def create_user_file(
        self,
        user_id: int,
        telegram_file_id: str,
        file_name: str | None,
        mime_type: str | None,
        file_size: int | None,
        ticket_id: int | None = None,
    ) -> UserFile:
        record = UserFile(
            user_id=user_id,
            ticket_id=ticket_id,
            telegram_file_id=telegram_file_id,
            file_name=file_name,
            mime_type=mime_type,
            file_size=file_size,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_user_file(self, file_id: int) -> UserFile | None:
        return await self.session.get(UserFile, file_id)

    async def list_for_user(self, user_id: int) -> list[UserFile]:
        result = await self.session.execute(
            select(UserFile).where(UserFile.user_id == user_id).order_by(UserFile.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_user_files(self) -> int:
        result = await self.session.execute(select(func.count(UserFile.id)))
        return result.scalar_one()

    async def set_status(self, user_file: UserFile, status: UserFileStatus) -> None:
        user_file.status = status
