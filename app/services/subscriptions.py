from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_repo import UserRepository
from app.services.content import ContentService
from app.utils.logging import get_logger

logger = get_logger(__name__)

ACTIVE_STATUSES = {"member", "administrator", "creator"}


class SubscriptionService:
    """Checks real Telegram channel subscription via the Bot API (getChatMember)."""

    def __init__(self, bot: Bot, session: AsyncSession) -> None:
        self.bot = bot
        self.session = session
        self.content = ContentService(session)

    async def is_subscribed(self, user_telegram_id: int) -> bool:
        channel_id = await self.content.get_channel_id()
        try:
            member = await self.bot.get_chat_member(chat_id=channel_id, user_id=user_telegram_id)
            if member.status in ACTIVE_STATUSES:
                return True
        except TelegramBadRequest as exc:
            logger.warning("subscription_check_failed", user_id=user_telegram_id, error=str(exc))

        # Для каналов с обязательным одобрением вступления реальное членство
        # может так и не наступить сразу - считаем достаточным сам факт того,
        # что пользователь отправил заявку (одобрит её админ позже вручную).
        if await self.content.get_require_join_approval():
            user_repo = UserRepository(self.session)
            user = await user_repo.get_by_telegram_id(user_telegram_id)
            if user is not None and user.channel_join_requested_at is not None:
                return True

        return False
