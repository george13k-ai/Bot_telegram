from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.support import SupportTicket
from app.database.models.tag import UserTag
from app.database.models.user import User
from app.database.models.user_file import UserFile


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_with_details(self, user_id: int) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.tags).selectinload(UserTag.tag),
                selectinload(User.files),
                selectinload(User.tickets),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        source: str | None = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            source=source,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def touch_activity(self, user: User, username: str | None, first_name: str | None, last_name: str | None) -> None:
        user.last_activity_at = datetime.now(timezone.utc)
        user.username = username
        user.first_name = first_name
        user.last_name = last_name

    async def set_blocked(self, user: User, is_blocked: bool) -> None:
        user.is_blocked = is_blocked

    async def set_subscribed(self, user: User, is_subscribed: bool) -> None:
        user.is_subscribed = is_subscribed

    async def search(self, query: str, limit: int = 10, offset: int = 0) -> list[User]:
        like = f"%{query}%"
        stmt = (
            select(User)
            .where(
                or_(
                    User.username.ilike(like),
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                )
            )
            .order_by(User.id.desc())
            .limit(limit)
            .offset(offset)
        )
        if query.lstrip("-").isdigit():
            stmt = select(User).where(
                or_(User.telegram_id == int(query), User.id == int(query))
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_paginated(self, limit: int = 10, offset: int = 0) -> list[User]:
        stmt = select(User).order_by(User.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def count_subscribed(self) -> int:
        result = await self.session.execute(select(func.count(User.id)).where(User.is_subscribed.is_(True)))
        return result.scalar_one()

    async def count_created_since(self, since: datetime) -> int:
        result = await self.session.execute(select(func.count(User.id)).where(User.created_at >= since))
        return result.scalar_one()

    async def list_by_audience_all(self) -> list[User]:
        result = await self.session.execute(select(User).where(User.is_blocked.is_(False)))
        return list(result.scalars().all())

    async def list_by_audience_activated(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.is_blocked.is_(False), User.is_subscribed.is_(True))
        )
        return list(result.scalars().all())

    async def list_by_audience_tag(self, tag_id: int) -> list[User]:
        stmt = (
            select(User)
            .join(UserTag, UserTag.user_id == User.id)
            .where(UserTag.tag_id == tag_id, User.is_blocked.is_(False))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_audience_file_sent(self) -> list[User]:
        stmt = (
            select(User)
            .join(UserFile, UserFile.user_id == User.id)
            .where(User.is_blocked.is_(False))
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_stuck_users(self, older_than: datetime, max_reminders: int) -> list[User]:
        """Users who subscribed but never opened a support ticket (e.g. never sent a PDF)."""
        no_ticket = ~exists().where(SupportTicket.user_id == User.id)
        stmt = select(User).where(
            User.is_subscribed.is_(True),
            User.is_blocked.is_(False),
            User.reminder_count < max_reminders,
            User.last_activity_at <= older_than,
            no_ticket,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def register_reminder_sent(self, user: User) -> None:
        user.reminder_count += 1
        user.last_reminder_at = datetime.now(timezone.utc)
