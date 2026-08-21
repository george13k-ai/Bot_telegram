from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user_event import EventType, UserEvent


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(self, user_id: int, event_type: EventType, meta: dict | None = None) -> UserEvent:
        event = UserEvent(user_id=user_id, event_type=event_type, meta=meta)
        self.session.add(event)
        await self.session.flush()
        return event

    async def count_by_type(self, event_type: EventType) -> int:
        result = await self.session.execute(
            select(func.count(UserEvent.id)).where(UserEvent.event_type == event_type)
        )
        return result.scalar_one()

    async def count_by_type_since(self, event_type: EventType, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count(UserEvent.id)).where(
                UserEvent.event_type == event_type, UserEvent.created_at >= since
            )
        )
        return result.scalar_one()

    async def list_for_user(self, user_id: int, limit: int = 50) -> list[UserEvent]:
        stmt = (
            select(UserEvent)
            .where(UserEvent.user_id == user_id)
            .order_by(UserEvent.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
