from __future__ import annotations

from app.database.models.support import MessageSender, MessageStatus, TicketStatus
from app.services.specialist import SpecialistService
from app.services.users import UsersService


async def _make_user(session, telegram_id: int):
    users = UsersService(session)
    user, _ = await users.get_or_create(telegram_id=telegram_id, username=None, first_name="U", last_name=None)
    await session.commit()
    return user


async def test_admin_reply_answers_ticket_and_pending_messages(session):
    user = await _make_user(session, 5001)
    specialist = SpecialistService(session)

    ticket = await specialist.create_specialist_ticket(user.id, "У меня вопрос")
    await session.commit()
    assert ticket.status == TicketStatus.WAITING_FOR_ADMIN

    await specialist.add_admin_reply(ticket, "Мы разберёмся и ответим сегодня")
    await session.commit()

    updated_ticket = await specialist.get_ticket_with_messages(ticket.id)
    assert updated_ticket.status == TicketStatus.ANSWERED

    admin_messages = [m for m in updated_ticket.messages if m.sender == MessageSender.ADMIN]
    user_messages = [m for m in updated_ticket.messages if m.sender == MessageSender.USER]

    assert len(admin_messages) == 1
    assert admin_messages[0].text == "Мы разберёмся и ответим сегодня"
    assert all(m.status == MessageStatus.ANSWERED for m in user_messages)
