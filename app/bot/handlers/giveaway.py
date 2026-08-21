from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.giveaway import giveaway_intro_keyboard, giveaway_post_keyboard, giveaway_result_keyboard
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.services.content import ContentService
from app.services.giveaway import GiveawayService
from app.services.subscriptions import SubscriptionService
from app.utils.callback_data import GiveawayCB, MainCB

router = Router(name="giveaway")


async def _ensure_active_giveaway(session: AsyncSession, content: ContentService):
    giveaways = GiveawayService(session)
    giveaway = await giveaways.get_active()
    if giveaway is None:
        description = await content.get_text("giveaway_message")
        giveaway = await giveaways.create(title="Ежемесячный розыгрыш", description=description)
    return giveaway


@router.callback_query(or_f(MainCB.filter(F.action == "giveaway"), GiveawayCB.filter(F.action == "open")))
async def on_giveaway_open(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    content = ContentService(session)
    giveaway = await _ensure_active_giveaway(session, content)

    events = EventRepository(session)
    await events.log(db_user.id, EventType.GIVEAWAY_OPENED)

    text = await content.get_text("giveaway_message")
    channel_url = await content.get_channel_url()
    keyboard = giveaway_intro_keyboard(giveaway.id, channel_url)

    if giveaway.image_file_id:
        await callback.message.answer_photo(photo=giveaway.image_file_id, caption=text, reply_markup=keyboard)
    else:
        await callback.message.answer(text, reply_markup=keyboard)

    await callback.answer()


@router.callback_query(GiveawayCB.filter(F.action == "post"))
async def on_giveaway_post(callback: CallbackQuery, session: AsyncSession, callback_data: GiveawayCB) -> None:
    content = ContentService(session)
    text = await content.get_text("giveaway_post_message")
    post_url = await content.get_giveaway_post_url()
    await callback.message.answer(text, reply_markup=giveaway_post_keyboard(callback_data.giveaway_id, post_url))
    await callback.answer()


@router.callback_query(GiveawayCB.filter(F.action == "join"))
async def on_giveaway_join(
    callback: CallbackQuery, session: AsyncSession, db_user: User, callback_data: GiveawayCB, bot
) -> None:
    if callback_data.giveaway_id is None:
        await callback.answer()
        return

    subscription_service = SubscriptionService(bot)
    if not await subscription_service.is_subscribed(db_user.telegram_id):
        await callback.answer(
            "Для участия нужно подписаться на канал. Подпишитесь и попробуйте снова.", show_alert=True
        )
        return

    giveaways = GiveawayService(session)
    result = await giveaways.join(callback_data.giveaway_id, db_user.id)

    events = EventRepository(session)

    if result.already_participant:
        await callback.message.answer(
            "Вы уже участвуете в розыгрыше! Ждите результатов в конце месяца.",
            reply_markup=giveaway_result_keyboard(),
        )
        await callback.answer()
        return

    await events.log(db_user.id, EventType.GIVEAWAY_JOINED)
    await callback.message.answer(
        "Вы успешно зарегистрированы в розыгрыше! Удачи 🍀",
        reply_markup=giveaway_result_keyboard(),
    )
    await callback.answer()
