from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.support import (
    MessageSender,
    MessageStatus,
    SupportMessage,
    SupportTicket,
    TicketSource,
    TicketStatus,
)
from app.database.repositories.support_repo import SupportRepository


class SpecialistService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SupportRepository(session)

    async def get_or_create_open_ticket(self, user_id: int, source: TicketSource) -> SupportTicket:
        ticket = await self.repo.get_open_ticket_for_user(user_id)
        if ticket is None:
            ticket = await self.repo.create_ticket(user_id, source, TicketStatus.NEW)
        return ticket

    async def create_specialist_ticket(self, user_id: int, message_text: str) -> SupportTicket:
        ticket = await self.repo.create_ticket(user_id, TicketSource.SPECIALIST_REQUEST, TicketStatus.WAITING_FOR_ADMIN)
        await self.repo.add_message(ticket.id, MessageSender.USER, message_text)
        return ticket

    async def register_pdf_upload(self, user_id: int) -> SupportTicket:
        ticket = await self.repo.get_open_ticket_for_user(user_id)
        if ticket is None:
            ticket = await self.repo.create_ticket(user_id, TicketSource.PDF_UPLOAD, TicketStatus.FILE_RECEIVED)
        else:
            await self.repo.set_status(ticket, TicketStatus.FILE_RECEIVED)
        return ticket

    async def mark_waiting_for_admin(self, ticket: SupportTicket) -> None:
        await self.repo.set_status(ticket, TicketStatus.WAITING_FOR_ADMIN)

    async def add_user_message(self, ticket_id: int, text: str) -> SupportMessage:
        return await self.repo.add_message(ticket_id, MessageSender.USER, text, MessageStatus.PENDING)

    async def add_admin_reply(self, ticket: SupportTicket, text: str) -> SupportMessage:
        message = await self.repo.add_message(ticket.id, MessageSender.ADMIN, text, MessageStatus.ANSWERED)
        await self.repo.mark_user_messages_answered(ticket.id)
        await self.repo.set_status(ticket, TicketStatus.ANSWERED)
        return message

    async def get_ticket(self, ticket_id: int) -> SupportTicket | None:
        return await self.repo.get_ticket(ticket_id)

    async def get_ticket_with_messages(self, ticket_id: int) -> SupportTicket | None:
        return await self.repo.get_ticket_with_messages(ticket_id)

    async def list_for_user(self, user_id: int) -> list[SupportTicket]:
        return await self.repo.list_for_user(user_id)

    async def list_recent_messages_for_user(self, user_id: int, limit: int = 10) -> list[SupportMessage]:
        return await self.repo.list_recent_messages_for_user(user_id, limit)

    async def set_calculated_amount(self, ticket: SupportTicket, amount: float | None) -> None:
        await self.repo.set_calculated_amount(ticket, amount)
