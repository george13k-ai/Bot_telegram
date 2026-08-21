from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.notification import Notification, NotificationType


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        type_: NotificationType,
        text: str,
        user_id: int | None = None,
        ticket_id: int | None = None,
    ) -> Notification:
        notification = Notification(type=type_, text=text, user_id=user_id, ticket_id=ticket_id)
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def get(self, notification_id: int) -> Notification | None:
        return await self.session.get(Notification, notification_id)

    async def mark_answered(self, notification: Notification, admin_id: int) -> None:
        notification.is_answered = True
        notification.admin_id = admin_id
        notification.answered_at = datetime.now(timezone.utc)

    async def list_recent(self, limit: int = 20, offset: int = 0) -> list[Notification]:
        stmt = select(Notification).order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_unanswered(self, limit: int = 20) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.is_answered.is_(False))
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
