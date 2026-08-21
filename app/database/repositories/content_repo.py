from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.content import Content


class ContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> Content | None:
        result = await self.session.execute(select(Content).where(Content.key == key))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Content]:
        result = await self.session.execute(select(Content).order_by(Content.key))
        return list(result.scalars().all())

    async def upsert(
        self,
        key: str,
        text: str | None = None,
        media_type: str | None = None,
        media_file_id: str | None = None,
        updated_by: int | None = None,
    ) -> Content:
        content = await self.get(key)
        if content is None:
            content = Content(key=key)
            self.session.add(content)
        if text is not None:
            content.text = text
        if media_type is not None:
            content.media_type = media_type
        if media_file_id is not None:
            content.media_file_id = media_file_id
        content.updated_by = updated_by
        await self.session.flush()
        return content
