from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import CallbackQuery, MessageReactionUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.giveaway import giveaway_intro_keyboard
from app.database.models.giveaway import Giveaway
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.services.content import ContentService
from app.services.giveaway import GiveawayService
from app.utils.callback_data import MainCB
from app.utils.logging import get_logger
from app.utils.telegram_links import parse_post_url

logger = get_logger(__name__)

router = Router(name="giveaway")


async def _get_active_giveaway(session: AsyncSession) -> Giveaway | None:
    giveaways = GiveawayService(session)
    return await giveaways.get_active()


@router.callback_query(MainCB.filter(F.action == "giveaway"))
async def on_giveaway_open(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    giveaway = await _get_active_giveaway(session)
    content = ContentService(session)

    if giveaway is None:
        await callback.message.answer(
            "На данный момент розыгрышей нет. Загляните позже — как только появится новый, вы сразу о нём узнаете!"
        )
        await callback.answer()
        return

    events = EventRepository(session)
    await events.log(db_user.id, EventType.GIVEAWAY_OPENED)

    description = giveaway.description or await content.get_text("giveaway_message")
    text = f"{description}\n\nЧтобы участвовать — поставьте любую реакцию под постом в канале."
    channel_url = await content.get_channel_url()
    post_url = giveaway.post_url or await content.get_giveaway_post_url()
    keyboard = giveaway_intro_keyboard(channel_url, post_url)

    if giveaway.image_file_id:
        await callback.message.answer_photo(photo=giveaway.image_file_id, caption=text, reply_markup=keyboard)
    else:
        await callback.message.answer(text, reply_markup=keyboard)

    await callback.answer()


@router.message_reaction()
async def on_giveaway_post_reaction(
    event: MessageReactionUpdated, session: AsyncSession, bot, db_user: User | None = None
) -> None:
    """
    Условие участия в розыгрыше - реакция на пост в канале (ТЗ: без кнопки
    "Участвовать" в боте). Ловим смену реакций на постах, привязанных к
    активным розыгрышам через их post_url, и регистрируем реагирующего
    пользователя как участника.
    """
    if not event.new_reaction:
        return  # реакцию убрали, а не поставили - участие не отзываем
    if db_user is None:
        return  # анонимная реакция от имени канала - не привязана к пользователю

    giveaways = GiveawayService(session)
    candidates = await giveaways.list_active_with_post_url()

    matched: Giveaway | None = None
    for giveaway in candidates:
        post = parse_post_url(giveaway.post_url)
        if post and post.message_id == event.message_id and post.matches_chat(event.chat.username, event.chat.id):
            matched = giveaway
            break

    if matched is None:
        return

    result = await giveaways.join(matched.id, db_user.id)
    if result.already_participant:
        return

    events = EventRepository(session)
    await events.log(db_user.id, EventType.GIVEAWAY_JOINED, {"via": "reaction", "giveaway_id": matched.id})

    try:
        await bot.send_message(
            chat_id=db_user.telegram_id,
            text=f"Вы участвуете в розыгрыше «{matched.title}»! Удачи 🍀",
        )
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        # Пользователь мог никогда не писать боту - тогда ЛС недоступны, это нормально.
        logger.info("giveaway_reaction_confirm_dm_failed", user_id=db_user.id, error=str(exc))
