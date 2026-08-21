from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.database.repositories.user_repo import UserRepository
from app.services.tags import TagService


class UsersService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)
        self.events = EventRepository(session)
        self.tags = TagService(session)

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        source: str | None = None,
    ) -> tuple[User, bool]:
        user = await self.repo.get_by_telegram_id(telegram_id)
        is_new = False
        if user is None:
            user = await self.repo.create(telegram_id, username, first_name, last_name, source)
            is_new = True
        else:
            await self.repo.touch_activity(user, username, first_name, last_name)
            if user.is_blocked:
                user.is_blocked = False
        return user, is_new

    async def register_start(self, user: User) -> None:
        await self.tags.mark_newbie(user.id)
        await self.events.log(user.id, EventType.START)

    async def block(self, user: User) -> None:
        await self.repo.set_blocked(user, True)

    async def unblock(self, user: User) -> None:
        await self.repo.set_blocked(user, False)

    async def set_subscribed(self, user: User, is_subscribed: bool) -> None:
        await self.repo.set_subscribed(user, is_subscribed)

    async def get_with_details(self, user_id: int) -> User | None:
        return await self.repo.get_with_details(user_id)

    async def search(self, query: str) -> list[User]:
        return await self.repo.search(query)

    async def list_paginated(self, limit: int = 10, offset: int = 0) -> list[User]:
        return await self.repo.list_paginated(limit, offset)

    async def count_all(self) -> int:
        return await self.repo.count_all()
