from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.instruction import why_keyboard
from app.bot.keyboards.subscription import subscription_keyboard
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.services.content import ContentService
from app.services.subscriptions import SubscriptionService
from app.services.users import UsersService
from app.utils.callback_data import MainCB, SubscriptionCB

router = Router(name="subscription")


@router.callback_query(MainCB.filter(F.action == "yes"))
async def on_main_yes(callback: CallbackQuery, session: AsyncSession) -> None:
    content = ContentService(session)
    text = await content.get_subscription_text()
    channel_url = await content.get_channel_url()
    await callback.message.answer(text, reply_markup=subscription_keyboard(channel_url))
    await callback.answer()


@router.callback_query(SubscriptionCB.filter(F.action == "check"))
async def on_subscription_check(callback: CallbackQuery, session: AsyncSession, db_user: User, bot) -> None:
    events = EventRepository(session)
    subscription_service = SubscriptionService(bot)
    is_subscribed = await subscription_service.is_subscribed(db_user.telegram_id)

    await events.log(db_user.id, EventType.SUBSCRIPTION_CHECK, {"result": is_subscribed})

    if not is_subscribed:
        await callback.answer(
            "Вы ещё не подписались на канал. Подпишитесь и нажмите «Проверить подписку» ещё раз.",
            show_alert=True,
        )
        return

    users_service = UsersService(session)
    was_subscribed = db_user.is_subscribed
    await users_service.set_subscribed(db_user, True)
    if not was_subscribed:
        await events.log(db_user.id, EventType.SUBSCRIBED)

    content = ContentService(session)
    thanks_text = await content.get_text("subscribed_message")
    await callback.message.answer(thanks_text)

    why_text = await content.get_text("why_message")
    await callback.message.answer(why_text, reply_markup=why_keyboard())
    await callback.answer()
