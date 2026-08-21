from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import with_home
from app.database.models.notification import NotificationType
from app.database.models.support import TicketSource
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.services.notifications import NotificationService
from app.services.specialist import SpecialistService
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router(name="fallback")


@router.message(StateFilter(None), F.text)
async def on_free_text(message: Message, session: AsyncSession, db_user: User, state: FSMContext, bot) -> None:
    """
    Any plain text message that isn't caught by an active FSM state or a more
    specific handler. If the user has an open support ticket, treat it as a
    follow-up message to the specialist (ТЗ п.38); otherwise gently point them
    back to the main menu.
    """
    specialist_service = SpecialistService(session)
    ticket = await specialist_service.get_or_create_open_ticket(db_user.id, TicketSource.MESSAGE)
    await specialist_service.add_user_message(ticket.id, message.text)
    await specialist_service.mark_waiting_for_admin(ticket)

    events = EventRepository(session)
    await events.log(db_user.id, EventType.MESSAGE_SENT)

    notifications = NotificationService(bot, session)
    summary = await notifications.build_user_summary(db_user, ticket, extra_note=f"Сообщение: {message.text}")
    await notifications.notify_admins(NotificationType.NEW_MESSAGE, db_user, summary, ticket_id=ticket.id)

    await message.answer(
        "Ваше сообщение получено, специалист ответит вам в ближайшее время.",
        reply_markup=with_home(InlineKeyboardBuilder()),
    )
