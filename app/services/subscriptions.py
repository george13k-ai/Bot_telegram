from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

ACTIVE_STATUSES = {"member", "administrator", "creator"}


class SubscriptionService:
    """Checks real Telegram channel subscription via the Bot API (getChatMember)."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def is_subscribed(self, user_telegram_id: int) -> bool:
        try:
            member = await self.bot.get_chat_member(
                chat_id=settings.REQUIRED_CHANNEL_ID, user_id=user_telegram_id
            )
        except TelegramBadRequest as exc:
            logger.warning("subscription_check_failed", user_id=user_telegram_id, error=str(exc))
            return False
        return member.status in ACTIVE_STATUSES
