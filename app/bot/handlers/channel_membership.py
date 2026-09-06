from __future__ import annotations

from aiogram import Router
from aiogram.types import ChatJoinRequest, ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content import ContentService
from app.services.subscriptions import ACTIVE_STATUSES
from app.services.users import UsersService
from app.services import scheduler as scheduler_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = Router(name="channel_membership")


async def _matches_configured_channel(content: ContentService, chat_id: int, chat_username: str | None) -> bool:
    configured = await content.get_channel_id()
    if isinstance(configured, str) and configured.startswith("@"):
        return chat_username is not None and f"@{chat_username}".lower() == configured.lower()
    try:
        return int(configured) == chat_id
    except (TypeError, ValueError):
        return False


@router.chat_join_request()
async def on_chat_join_request(event: ChatJoinRequest, session: AsyncSession) -> None:
    """
    Для приватных каналов, куда нужно одобрение админа: сам факт заявки на
    вступление (без ожидания фактического одобрения) может засчитываться как
    "подписка выполнена" - см. SubscriptionService.is_subscribed и настройку
    "Канал требует одобрения вступления".
    """
    content = ContentService(session)
    if not await _matches_configured_channel(content, event.chat.id, event.chat.username):
        return

    users_service = UsersService(session)
    user, _ = await users_service.get_or_create(
        telegram_id=event.from_user.id,
        username=event.from_user.username,
        first_name=event.from_user.first_name,
        last_name=event.from_user.last_name,
    )
    await users_service.set_channel_join_requested(user)
    logger.info("channel_join_request_received", user_id=user.id, telegram_id=user.telegram_id)


@router.chat_member()
async def on_channel_membership_changed(event: ChatMemberUpdated, session: AsyncSession, scheduler) -> None:
    """Ловим момент, когда пользователь покидает обязательный канал, и планируем напоминание."""
    content = ContentService(session)
    if not await _matches_configured_channel(content, event.chat.id, event.chat.username):
        return

    was_active = event.old_chat_member.status in ACTIVE_STATUSES
    is_active = event.new_chat_member.status in ACTIVE_STATUSES
    if not (was_active and not is_active):
        return  # интересует только переход "был подписан -> отписался/исключён"

    target = event.new_chat_member.user
    users_service = UsersService(session)
    user, _ = await users_service.get_or_create(
        telegram_id=target.id,
        username=target.username,
        first_name=target.first_name,
        last_name=target.last_name,
    )
    await users_service.set_subscribed(user, False)

    minutes = await content.get_unsubscribe_reminder_minutes()
    scheduler_service.schedule_unsubscribe_reminder(scheduler, user.id, minutes)
    logger.info("channel_unsubscribed", user_id=user.id, telegram_id=user.telegram_id, reminder_in_minutes=minutes)
