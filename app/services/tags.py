from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.tag import Tag
from app.database.repositories.tag_repo import TagRepository

TAG_NEWBIE = "Новичок"
TAG_PRO = "Профи"


class TagService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TagRepository(session)

    async def assign_by_name(self, user_id: int, name: str) -> None:
        tag = await self.repo.get_or_create(name)
        await self.repo.assign(user_id, tag.id)

    async def remove_by_name(self, user_id: int, name: str) -> None:
        tag = await self.repo.get_or_create(name)
        await self.repo.remove(user_id, tag.id)

    async def mark_newbie(self, user_id: int) -> None:
        await self.assign_by_name(user_id, TAG_NEWBIE)

    async def mark_pro(self, user_id: int) -> None:
        await self.assign_by_name(user_id, TAG_PRO)

    async def list_all(self) -> list[Tag]:
        return await self.repo.list_all()

    async def list_for_user(self, user_id: int) -> list[Tag]:
        return await self.repo.list_for_user(user_id)

    async def get_by_id(self, tag_id: int) -> Tag | None:
        return await self.repo.get_by_id(tag_id)
