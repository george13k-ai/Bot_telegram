from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import with_home
from app.bot.states.specialist import SpecialistForm
from app.database.models.notification import NotificationType
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.services.content import ContentService
from app.services.notifications import NotificationService
from app.services.specialist import SpecialistService
from app.utils.callback_data import MainCB, SpecialistCB
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router(name="specialist")


@router.callback_query(or_f(MainCB.filter(F.action == "specialist"), SpecialistCB.filter(F.action == "create")))
async def on_specialist_start(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    content = ContentService(session)
    text = await content.get_text("specialist_message")
    await callback.message.answer(text, reply_markup=with_home(InlineKeyboardBuilder()))
    await state.set_state(SpecialistForm.waiting_for_message)
    await callback.answer()


@router.message(SpecialistForm.waiting_for_message, F.text)
async def on_specialist_message(message: Message, session: AsyncSession, db_user: User, state: FSMContext, bot) -> None:
    specialist_service = SpecialistService(session)
    ticket = await specialist_service.create_specialist_ticket(db_user.id, message.text)

    events = EventRepository(session)
    await events.log(db_user.id, EventType.SPECIALIST_REQUESTED)
    await events.log(db_user.id, EventType.MESSAGE_SENT)

    notifications = NotificationService(bot, session)
    summary = await notifications.build_user_summary(db_user, ticket, extra_note=f"Сообщение: {message.text}")
    await notifications.notify_admins(NotificationType.NEW_TICKET, db_user, summary, ticket_id=ticket.id)

    await message.answer(
        "Ваше сообщение передано специалисту. Мы ответим вам в ближайшее время.",
        reply_markup=with_home(InlineKeyboardBuilder()),
    )
    await state.clear()


@router.message(SpecialistForm.waiting_for_message)
async def on_specialist_wrong_content(message: Message) -> None:
    await message.answer("Пожалуйста, опишите ваш вопрос текстом.")
