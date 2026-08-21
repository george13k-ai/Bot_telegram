from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.mailing import (
    AudienceType,
    Mailing,
    MailingRecipient,
    MailingStatus,
    RecipientStatus,
)


class MailingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        text: str,
        photo_file_id: str | None,
        audience_type: AudienceType,
        audience_filter: dict | None,
        scheduled_at: datetime | None,
        status: MailingStatus,
        created_by: int,
    ) -> Mailing:
        mailing = Mailing(
            text=text,
            photo_file_id=photo_file_id,
            audience_type=audience_type,
            audience_filter=audience_filter,
            scheduled_at=scheduled_at,
            status=status,
            created_by=created_by,
        )
        self.session.add(mailing)
        await self.session.flush()
        return mailing

    async def get(self, mailing_id: int) -> Mailing | None:
        return await self.session.get(Mailing, mailing_id)

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Mailing]:
        stmt = select(Mailing).order_by(Mailing.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_due(self, now: datetime) -> list[Mailing]:
        stmt = select(Mailing).where(
            Mailing.status == MailingStatus.SCHEDULED, Mailing.scheduled_at <= now
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def set_status(self, mailing: Mailing, status: MailingStatus) -> None:
        mailing.status = status

    async def add_recipient(self, mailing_id: int, user_id: int) -> MailingRecipient:
        recipient = MailingRecipient(mailing_id=mailing_id, user_id=user_id)
        self.session.add(recipient)
        return recipient

    async def bulk_add_recipients(self, mailing_id: int, user_ids: list[int]) -> None:
        self.session.add_all(
            [MailingRecipient(mailing_id=mailing_id, user_id=uid) for uid in user_ids]
        )
        await self.session.flush()

    async def list_pending_recipients(self, mailing_id: int) -> list[MailingRecipient]:
        stmt = (
            select(MailingRecipient)
            .where(MailingRecipient.mailing_id == mailing_id, MailingRecipient.status == RecipientStatus.PENDING)
            .options(selectinload(MailingRecipient.user))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_recipient(
        self, recipient: MailingRecipient, status: RecipientStatus, sent_at: datetime | None = None
    ) -> None:
        recipient.status = status
        recipient.sent_at = sent_at

    async def update_counters(self, mailing: Mailing, sent: int, failed: int, blocked: int, total: int) -> None:
        mailing.sent = sent
        mailing.failed = failed
        mailing.blocked = blocked
        mailing.total = total

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(Mailing.id)))
        return result.scalar_one()
