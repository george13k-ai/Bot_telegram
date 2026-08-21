from __future__ import annotations

import asyncio
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.mailing import AudienceType, Mailing, MailingStatus, RecipientStatus
from app.database.models.user import User
from app.database.repositories.mailing_repo import MailingRepository
from app.database.repositories.user_repo import UserRepository
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Telegram tolerates roughly 30 messages/sec globally to distinct chats.
# We stay well under that to leave headroom for other bot traffic.
MAX_CONCURRENT_SENDS = 15
DELAY_BETWEEN_SENDS = 0.05


class MailingService:
    def __init__(self, bot: Bot, session: AsyncSession) -> None:
        self.bot = bot
        self.session = session
        self.repo = MailingRepository(session)
        self.user_repo = UserRepository(session)

    async def build_audience(self, audience_type: AudienceType, audience_filter: dict | None) -> list[User]:
        if audience_type == AudienceType.ALL:
            return await self.user_repo.list_by_audience_all()
        if audience_type == AudienceType.ACTIVATED:
            return await self.user_repo.list_by_audience_activated()
        if audience_type == AudienceType.TAG:
            tag_id = (audience_filter or {}).get("tag_id")
            if tag_id is None:
                return []
            return await self.user_repo.list_by_audience_tag(int(tag_id))
        if audience_type == AudienceType.FILE_SENT:
            return await self.user_repo.list_by_audience_file_sent()
        return []

    async def create_draft(
        self,
        text: str,
        photo_file_id: str | None,
        created_by: int,
    ) -> Mailing:
        return await self.repo.create(
            text=text,
            photo_file_id=photo_file_id,
            audience_type=AudienceType.ALL,
            audience_filter=None,
            scheduled_at=None,
            status=MailingStatus.DRAFT,
            created_by=created_by,
        )

    async def get(self, mailing_id: int) -> Mailing | None:
        return await self.repo.get(mailing_id)

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Mailing]:
        return await self.repo.list_all(limit, offset)

    async def list_due(self, now: datetime) -> list[Mailing]:
        return await self.repo.list_due(now)

    async def finalize_setup(
        self,
        mailing: Mailing,
        audience_type: AudienceType,
        audience_filter: dict | None,
        scheduled_at: datetime | None,
    ) -> int:
        mailing.audience_type = audience_type
        mailing.audience_filter = audience_filter
        mailing.scheduled_at = scheduled_at
        mailing.status = MailingStatus.SCHEDULED if scheduled_at else MailingStatus.SENDING

        users = await self.build_audience(audience_type, audience_filter)
        await self.repo.bulk_add_recipients(mailing.id, [u.id for u in users])
        await self.repo.update_counters(mailing, sent=0, failed=0, blocked=0, total=len(users))
        return len(users)

    async def cancel(self, mailing: Mailing) -> None:
        await self.repo.set_status(mailing, MailingStatus.CANCELLED)

    async def send_now(self, mailing_id: int) -> Mailing:
        mailing = await self.repo.get(mailing_id)
        if mailing is None:
            raise ValueError(f"Mailing {mailing_id} not found")

        await self.repo.set_status(mailing, MailingStatus.SENDING)
        await self.session.commit()

        recipients = await self.repo.list_pending_recipients(mailing_id)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_SENDS)

        sent = mailing.sent
        failed = mailing.failed
        blocked = mailing.blocked

        async def send_one(recipient) -> None:
            nonlocal sent, failed, blocked
            async with semaphore:
                user = recipient.user
                try:
                    if mailing.photo_file_id:
                        await self.bot.send_photo(
                            chat_id=user.telegram_id, photo=mailing.photo_file_id, caption=mailing.text
                        )
                    else:
                        await self.bot.send_message(chat_id=user.telegram_id, text=mailing.text)
                    recipient.status = RecipientStatus.SENT
                    recipient.sent_at = datetime.now()
                    sent += 1
                except TelegramRetryAfter as exc:
                    await asyncio.sleep(exc.retry_after)
                    try:
                        if mailing.photo_file_id:
                            await self.bot.send_photo(
                                chat_id=user.telegram_id, photo=mailing.photo_file_id, caption=mailing.text
                            )
                        else:
                            await self.bot.send_message(chat_id=user.telegram_id, text=mailing.text)
                        recipient.status = RecipientStatus.SENT
                        recipient.sent_at = datetime.now()
                        sent += 1
                    except (TelegramForbiddenError, TelegramBadRequest):
                        recipient.status = RecipientStatus.FAILED
                        failed += 1
                except TelegramForbiddenError:
                    recipient.status = RecipientStatus.BLOCKED
                    blocked += 1
                except TelegramBadRequest as exc:
                    logger.warning("mailing_send_failed", mailing_id=mailing_id, user_id=user.id, error=str(exc))
                    recipient.status = RecipientStatus.FAILED
                    failed += 1
                await asyncio.sleep(DELAY_BETWEEN_SENDS)

        await asyncio.gather(*(send_one(r) for r in recipients))

        await self.repo.update_counters(mailing, sent=sent, failed=failed, blocked=blocked, total=mailing.total)
        await self.repo.set_status(mailing, MailingStatus.COMPLETED)
        await self.session.commit()
        return mailing
