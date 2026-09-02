from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.main import start_menu_keyboard
from app.database.models.notification import NotificationType
from app.database.models.user import User
from app.services.content import ContentService
from app.services.giveaway import GiveawayService
from app.services.notifications import NotificationService
from app.services.users import UsersService
from app.utils.callback_data import MainCB

router = Router(name="start")


async def _has_active_giveaway(session: AsyncSession) -> bool:
    return await GiveawayService(session).get_active() is not None


@router.message(CommandStart())
async def cmd_start(
    message: Message, session: AsyncSession, db_user: User, is_new_user: bool, state: FSMContext, bot
) -> None:
    await state.clear()

    users_service = UsersService(session)
    if is_new_user:
        source = None
        args = message.text.split(maxsplit=1)
        if len(args) > 1:
            source = args[1]
            db_user.source = source
        await users_service.register_start(db_user)

        notifications = NotificationService(bot, session)
        summary = await notifications.build_user_summary(db_user, ticket=None, extra_note="Новый пользователь активировал бота.")
        await notifications.notify_admins(NotificationType.NEW_USER, db_user, summary)

    content = ContentService(session)
    text = await content.get_text("start_message")
    await message.answer(text, reply_markup=start_menu_keyboard(show_giveaway=await _has_active_giveaway(session)))


@router.callback_query(MainCB.filter(F.action == "home"))
async def on_home(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    content = ContentService(session)
    text = await content.get_text("start_message")
    await callback.message.answer(
        text, reply_markup=start_menu_keyboard(show_giveaway=await _has_active_giveaway(session))
    )
    await callback.answer()
