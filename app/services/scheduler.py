from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database.models.notification import NotificationType
from app.database.models.user import User
from app.database.repositories.support_repo import SupportRepository
from app.database.repositories.user_repo import UserRepository
from app.database.session import get_session
from app.services.content import ContentService
from app.services.notifications import NotificationService
from app.utils.callback_data import MainCB
from app.utils.logging import get_logger

logger = get_logger(__name__)

_bot: Bot | None = None


def set_bot(bot: Bot) -> None:
    global _bot
    _bot = bot


def _specialist_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Написать специалисту", callback_data=MainCB(action="specialist").pack())]
        ]
    )


async def admin_reminder_job() -> None:
    """Nudge admins about support tickets waiting too long for a reply (ТЗ п.18/58)."""
    if _bot is None:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.REMINDER_DELAY_SECONDS)
    async with get_session() as session:
        support_repo = SupportRepository(session)
        tickets = await support_repo.list_stale_waiting_tickets(cutoff, settings.MAX_REMINDERS)
        notification_service = NotificationService(_bot, session)
        for ticket in tickets:
            user = await session.get(User, ticket.user_id)
            if user is None:
                continue
            text = await notification_service.build_user_summary(
                user, ticket, extra_note="⏰ Напоминание: заявка ожидает ответа администратора."
            )
            await notification_service.notify_admins(NotificationType.OTHER, user, text, ticket_id=ticket.id)
            await support_repo.register_reminder_sent(ticket)
        await session.commit()


async def user_reminder_job() -> None:
    """Nudge users stuck mid-funnel (subscribed but never sent a file/opened a ticket)."""
    if _bot is None:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.REMINDER_DELAY_SECONDS)
    async with get_session() as session:
        user_repo = UserRepository(session)
        content_service = ContentService(session)
        users = await user_repo.list_stuck_users(cutoff, settings.MAX_REMINDERS)
        text = await content_service.get_text("reminder_user_message")
        keyboard = _specialist_keyboard()
        for user in users:
            try:
                await _bot.send_message(user.telegram_id, text, reply_markup=keyboard)
            except TelegramForbiddenError:
                user.is_blocked = True
            except TelegramBadRequest as exc:
                logger.warning("user_reminder_failed", user_id=user.id, error=str(exc))
            await user_repo.register_reminder_sent(user)
        await session.commit()


async def send_scheduled_mailing_job(mailing_id: int) -> None:
    if _bot is None:
        return
    # Local import avoids a circular import (mailings -> scheduler is not needed,
    # but keeps this module importable before the mailing service is defined).
    from app.services.mailings import MailingService

    async with get_session() as session:
        mailing_service = MailingService(_bot, session)
        try:
            await mailing_service.send_now(mailing_id)
        except Exception:
            logger.exception("scheduled_mailing_failed", mailing_id=mailing_id)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
    scheduler.add_jobstore(SQLAlchemyJobStore(url=settings.database_url_sync), alias="default")
    return scheduler


def register_periodic_jobs(scheduler: AsyncIOScheduler) -> None:
    scheduler.add_job(
        admin_reminder_job, "interval", seconds=60, id="admin_reminder_job", replace_existing=True
    )
    scheduler.add_job(
        user_reminder_job, "interval", seconds=60, id="user_reminder_job", replace_existing=True
    )


def schedule_mailing(scheduler: AsyncIOScheduler, mailing_id: int, run_date: datetime) -> None:
    scheduler.add_job(
        send_scheduled_mailing_job,
        "date",
        run_date=run_date,
        args=[mailing_id],
        id=f"mailing_{mailing_id}",
        replace_existing=True,
    )


def schedule_mailing_now(scheduler: AsyncIOScheduler, mailing_id: int) -> None:
    scheduler.add_job(
        send_scheduled_mailing_job,
        args=[mailing_id],
        id=f"mailing_{mailing_id}_now",
        replace_existing=True,
    )


def cancel_scheduled_mailing(scheduler: AsyncIOScheduler, mailing_id: int) -> None:
    job_id = f"mailing_{mailing_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
