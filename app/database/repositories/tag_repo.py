from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.tag import Tag, UserTag


class TagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, name: str) -> Tag:
        result = await self.session.execute(select(Tag).where(Tag.name == name))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = Tag(name=name)
            self.session.add(tag)
            await self.session.flush()
        return tag

    async def list_all(self) -> list[Tag]:
        result = await self.session.execute(select(Tag).order_by(Tag.name))
        return list(result.scalars().all())

    async def get_by_id(self, tag_id: int) -> Tag | None:
        return await self.session.get(Tag, tag_id)

    async def user_has_tag(self, user_id: int, tag_id: int) -> bool:
        result = await self.session.execute(
            select(UserTag).where(UserTag.user_id == user_id, UserTag.tag_id == tag_id)
        )
        return result.scalar_one_or_none() is not None

    async def assign(self, user_id: int, tag_id: int) -> None:
        if await self.user_has_tag(user_id, tag_id):
            return
        self.session.add(UserTag(user_id=user_id, tag_id=tag_id))
        await self.session.flush()

    async def remove(self, user_id: int, tag_id: int) -> None:
        result = await self.session.execute(
            select(UserTag).where(UserTag.user_id == user_id, UserTag.tag_id == tag_id)
        )
        user_tag = result.scalar_one_or_none()
        if user_tag is not None:
            await self.session.delete(user_tag)
            await self.session.flush()

    async def list_for_user(self, user_id: int) -> list[Tag]:
        stmt = (
            select(Tag)
            .join(UserTag, UserTag.tag_id == Tag.id)
            .where(UserTag.user_id == user_id)
            .options(selectinload(Tag.users))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
