from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.support import (
    MessageSender,
    MessageStatus,
    SupportMessage,
    SupportTicket,
    TicketSource,
    TicketStatus,
)


class SupportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_ticket(self, user_id: int, source: TicketSource, status: TicketStatus) -> SupportTicket:
        ticket = SupportTicket(user_id=user_id, source=source, status=status)
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def get_ticket(self, ticket_id: int) -> SupportTicket | None:
        return await self.session.get(SupportTicket, ticket_id)

    async def get_ticket_with_messages(self, ticket_id: int) -> SupportTicket | None:
        stmt = (
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .options(selectinload(SupportTicket.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_ticket_for_user(self, user_id: int) -> SupportTicket | None:
        stmt = (
            select(SupportTicket)
            .where(
                SupportTicket.user_id == user_id,
                SupportTicket.status.notin_([TicketStatus.CLOSED]),
            )
            .order_by(SupportTicket.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[SupportTicket]:
        stmt = (
            select(SupportTicket)
            .where(SupportTicket.user_id == user_id)
            .order_by(SupportTicket.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent_messages_for_user(self, user_id: int, limit: int = 10) -> list[SupportMessage]:
        stmt = (
            select(SupportMessage)
            .join(SupportTicket, SupportMessage.ticket_id == SupportTicket.id)
            .where(SupportTicket.user_id == user_id)
            .order_by(SupportMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def set_status(self, ticket: SupportTicket, status: TicketStatus) -> None:
        ticket.status = status

    async def set_calculated_amount(self, ticket: SupportTicket, amount: float | None) -> None:
        ticket.calculated_amount = amount

    async def add_message(
        self, ticket_id: int, sender: MessageSender, text: str | None, status: MessageStatus = MessageStatus.PENDING
    ) -> SupportMessage:
        message = SupportMessage(ticket_id=ticket_id, sender=sender, text=text, status=status)
        self.session.add(message)
        await self.session.flush()
        return message

    async def mark_user_messages_answered(self, ticket_id: int) -> None:
        stmt = select(SupportMessage).where(
            SupportMessage.ticket_id == ticket_id,
            SupportMessage.sender == MessageSender.USER,
            SupportMessage.status == MessageStatus.PENDING,
        )
        result = await self.session.execute(stmt)
        for message in result.scalars().all():
            message.status = MessageStatus.ANSWERED

    async def list_stale_waiting_tickets(self, older_than: datetime, max_reminders: int) -> list[SupportTicket]:
        stmt = select(SupportTicket).where(
            SupportTicket.status == TicketStatus.WAITING_FOR_ADMIN,
            SupportTicket.updated_at <= older_than,
            SupportTicket.reminder_count < max_reminders,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def register_reminder_sent(self, ticket: SupportTicket) -> None:
        ticket.reminder_count += 1
        ticket.last_reminder_at = datetime.now(timezone.utc)

    async def count_total(self) -> int:
        result = await self.session.execute(select(func.count(SupportTicket.id)))
        return result.scalar_one()
