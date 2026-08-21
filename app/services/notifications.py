from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models.notification import Notification, NotificationType
from app.database.models.support import SupportTicket
from app.database.models.user import User
from app.database.repositories.notification_repo import NotificationRepository
from app.database.repositories.tag_repo import TagRepository
from app.services.content import ContentService
from app.utils.callback_data import NotificationCB
from app.utils.formatting import format_amount, format_datetime, format_user_mention
from app.utils.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    def __init__(self, bot: Bot, session: AsyncSession) -> None:
        self.bot = bot
        self.session = session
        self.repo = NotificationRepository(session)
        self.tag_repo = TagRepository(session)
        self.content_service = ContentService(session)

    async def _target_chat_ids(self) -> list[int]:
        ids = list(settings.admin_ids)
        specialist_chat_id = await self.content_service.get_specialist_chat_id()
        if specialist_chat_id is not None and specialist_chat_id not in ids:
            ids.append(specialist_chat_id)
        return ids

    async def _build_reply_keyboard(self, notification_id: int, ticket_id: int | None, user_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Ответить",
                        callback_data=NotificationCB(
                            action="reply",
                            notification_id=notification_id,
                            ticket_id=ticket_id,
                            user_id=user_id,
                        ).pack(),
                    )
                ]
            ]
        )

    async def build_user_summary(self, user: User, ticket: SupportTicket | None, extra_note: str = "") -> str:
        tags = await self.tag_repo.list_for_user(user.id)
        tags_line = " ".join(f"#{t.name}" for t in tags) if tags else ""

        lines = [
            f"Пользователь №{user.id}: {format_user_mention(user)}",
            "",
            f"Активировал бота {format_datetime(user.created_at)}",
        ]
        if tags_line:
            lines.append("")
            lines.append(tags_line)
        if ticket is not None:
            lines.append("")
            lines.append(f"Страховка на сумму: {format_amount(float(ticket.calculated_amount) if ticket.calculated_amount else None)}")
            lines.append(f"Статус: {ticket.status_label}")
        if extra_note:
            lines.append("")
            lines.append(extra_note)
        return "\n".join(lines)

    async def notify_admins(
        self,
        type_: NotificationType,
        user: User,
        summary_text: str,
        ticket_id: int | None = None,
        document_file_id: str | None = None,
    ) -> Notification:
        notification = await self.repo.create(type_, summary_text, user_id=user.id, ticket_id=ticket_id)
        keyboard = await self._build_reply_keyboard(notification.id, ticket_id, user.id)

        for chat_id in await self._target_chat_ids():
            await self._send_with_retry(chat_id, summary_text, keyboard, document_file_id)

        return notification

    async def _send_with_retry(
        self, chat_id: int, text: str, keyboard: InlineKeyboardMarkup, document_file_id: str | None
    ) -> None:
        try:
            if document_file_id:
                await self.bot.send_document(
                    chat_id=chat_id,
                    document=document_file_id,
                    caption=text[:1024],
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            else:
                await self.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        except TelegramRetryAfter as exc:
            logger.warning("notify_admin_retry_after", chat_id=chat_id, retry_after=exc.retry_after)
        except (TelegramForbiddenError, TelegramBadRequest) as exc:
            logger.warning("notify_admin_failed", chat_id=chat_id, error=str(exc))

    async def mark_answered(self, notification_id: int, admin_id: int) -> Notification | None:
        notification = await self.repo.get(notification_id)
        if notification is None:
            return None
        await self.repo.mark_answered(notification, admin_id)
        return notification
