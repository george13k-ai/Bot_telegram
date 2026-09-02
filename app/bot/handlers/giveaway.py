from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.giveaway import giveaway_intro_keyboard
from app.database.models.giveaway import Giveaway
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.services.content import ContentService
from app.services.giveaway import GiveawayService
from app.utils.callback_data import MainCB

router = Router(name="giveaway")


async def _ensure_active_giveaway(session: AsyncSession, content: ContentService) -> Giveaway:
    giveaways = GiveawayService(session)
    giveaway = await giveaways.get_active()
    if giveaway is None:
        description = await content.get_text("giveaway_message")
        giveaway = await giveaways.create(title="Ежемесячный розыгрыш", description=description)
    return giveaway


@router.callback_query(MainCB.filter(F.action == "giveaway"))
async def on_giveaway_open(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    content = ContentService(session)
    giveaway = await _ensure_active_giveaway(session, content)

    events = EventRepository(session)
    await events.log(db_user.id, EventType.GIVEAWAY_OPENED)

    text = await content.get_text("giveaway_message")
    channel_url = await content.get_channel_url()
    post_url = giveaway.post_url or await content.get_giveaway_post_url()
    keyboard = giveaway_intro_keyboard(channel_url, post_url)

    if giveaway.image_file_id:
        await callback.message.answer_photo(photo=giveaway.image_file_id, caption=text, reply_markup=keyboard)
    else:
        await callback.message.answer(text, reply_markup=keyboard)

    await callback.answer()
