from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.giveaway import GiveawayParticipant
from app.database.models.mailing import Mailing
from app.database.models.support import SupportTicket
from app.database.models.user_event import EventType
from app.database.models.user_file import UserFile
from app.database.repositories.event_repo import EventRepository
from app.database.repositories.user_repo import UserRepository


@dataclass
class BotStatistics:
    total_users: int
    new_users_24h: int
    new_users_7d: int
    activated_users: int
    subscribed_users: int
    files_sent: int
    tickets_total: int
    giveaway_participants: int
    mailings_total: int
    messages_delivered: int
    delivery_errors: int


class StatisticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.event_repo = EventRepository(session)

    async def collect(self) -> BotStatistics:
        now = datetime.now(timezone.utc)

        total_users = await self.user_repo.count_all()
        new_24h = await self.user_repo.count_created_since(now - timedelta(hours=24))
        new_7d = await self.user_repo.count_created_since(now - timedelta(days=7))
        activated = await self.event_repo.count_by_type(EventType.START)
        subscribed = await self.user_repo.count_subscribed()

        files_sent = (await self.session.execute(select(func.count(UserFile.id)))).scalar_one()
        tickets_total = (await self.session.execute(select(func.count(SupportTicket.id)))).scalar_one()
        giveaway_participants = (
            await self.session.execute(select(func.count(GiveawayParticipant.id)))
        ).scalar_one()
        mailings_total = (await self.session.execute(select(func.count(Mailing.id)))).scalar_one()
        delivered = (await self.session.execute(select(func.coalesce(func.sum(Mailing.sent), 0)))).scalar_one()
        errors = (
            await self.session.execute(
                select(func.coalesce(func.sum(Mailing.failed + Mailing.blocked), 0))
            )
        ).scalar_one()

        return BotStatistics(
            total_users=total_users,
            new_users_24h=new_24h,
            new_users_7d=new_7d,
            activated_users=activated,
            subscribed_users=subscribed,
            files_sent=files_sent,
            tickets_total=tickets_total,
            giveaway_participants=giveaway_participants,
            mailings_total=mailings_total,
            messages_delivered=int(delivered),
            delivery_errors=int(errors),
        )

    def format_report(self, stats: BotStatistics) -> str:
        return (
            "<b>Статистика бота</b>\n\n"
            f"Всего пользователей: {stats.total_users}\n"
            f"Новых за 24ч: {stats.new_users_24h}\n"
            f"Новых за 7 дней: {stats.new_users_7d}\n"
            f"Активированных пользователей: {stats.activated_users}\n"
            f"Подписались на канал: {stats.subscribed_users}\n"
            f"Отправлено файлов: {stats.files_sent}\n"
            f"Обращений (заявок): {stats.tickets_total}\n"
            f"Участников розыгрыша: {stats.giveaway_participants}\n"
            f"Рассылок создано: {stats.mailings_total}\n"
            f"Доставлено сообщений в рассылках: {stats.messages_delivered}\n"
            f"Ошибок доставки: {stats.delivery_errors}"
        )
