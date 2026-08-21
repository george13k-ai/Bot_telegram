from __future__ import annotations

from app.database.models.support import TicketSource, TicketStatus
from app.services.specialist import SpecialistService
from app.services.users import UsersService


async def _make_user(session, telegram_id: int):
    users = UsersService(session)
    user, _ = await users.get_or_create(telegram_id=telegram_id, username=None, first_name="U", last_name=None)
    await session.commit()
    return user


async def test_create_specialist_ticket(session):
    user = await _make_user(session, 4001)
    specialist = SpecialistService(session)

    ticket = await specialist.create_specialist_ticket(user.id, "Помогите разобраться")
    await session.commit()

    assert ticket.source == TicketSource.SPECIALIST_REQUEST
    assert ticket.status == TicketStatus.WAITING_FOR_ADMIN

    loaded = await specialist.get_ticket_with_messages(ticket.id)
    assert len(loaded.messages) == 1
    assert loaded.messages[0].text == "Помогите разобраться"


async def test_register_pdf_upload_creates_ticket_with_file_received_status(session):
    user = await _make_user(session, 4002)
    specialist = SpecialistService(session)

    ticket = await specialist.register_pdf_upload(user.id)
    await session.commit()

    assert ticket.status == TicketStatus.FILE_RECEIVED
    assert ticket.source == TicketSource.PDF_UPLOAD


async def test_register_pdf_upload_reuses_open_ticket(session):
    user = await _make_user(session, 4003)
    specialist = SpecialistService(session)

    first_ticket = await specialist.create_specialist_ticket(user.id, "Вопрос")
    await session.commit()

    second_ticket = await specialist.register_pdf_upload(user.id)
    await session.commit()

    assert second_ticket.id == first_ticket.id
    assert second_ticket.status == TicketStatus.FILE_RECEIVED
