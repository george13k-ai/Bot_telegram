from __future__ import annotations

from datetime import datetime, timedelta

from app.database.models.mailing import AudienceType, MailingStatus
from app.services.mailings import MailingService
from app.services.users import UsersService


async def _make_user(session, telegram_id: int, subscribed: bool = False):
    users = UsersService(session)
    user, _ = await users.get_or_create(telegram_id=telegram_id, username=None, first_name="U", last_name=None)
    if subscribed:
        await users.set_subscribed(user, True)
    await session.commit()
    return user


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs) -> None:
        self.sent.append((chat_id, text))

    async def send_photo(self, chat_id: int, photo: str, caption: str, **kwargs) -> None:
        self.sent.append((chat_id, caption))


async def test_create_draft_and_finalize_all_audience(session):
    await _make_user(session, 6001, subscribed=True)
    await _make_user(session, 6002, subscribed=False)

    service = MailingService(FakeBot(), session)
    mailing = await service.create_draft(text="Привет всем!", photo_file_id=None, created_by=111111)
    await session.commit()

    assert mailing.status == MailingStatus.DRAFT

    count = await service.finalize_setup(mailing, AudienceType.ALL, None, scheduled_at=None)
    await session.commit()

    assert count == 2
    assert mailing.status == MailingStatus.SENDING
    assert mailing.total == 2


async def test_finalize_setup_activated_audience_only(session):
    await _make_user(session, 6003, subscribed=True)
    await _make_user(session, 6004, subscribed=False)

    service = MailingService(FakeBot(), session)
    mailing = await service.create_draft(text="Только подписанным", photo_file_id=None, created_by=111111)
    await session.commit()

    count = await service.finalize_setup(mailing, AudienceType.ACTIVATED, None, scheduled_at=None)
    await session.commit()

    assert count == 1


async def test_finalize_setup_with_schedule_marks_scheduled(session):
    await _make_user(session, 6005, subscribed=True)

    service = MailingService(FakeBot(), session)
    mailing = await service.create_draft(text="Позже", photo_file_id=None, created_by=111111)
    await session.commit()

    run_at = datetime.now() + timedelta(hours=2)
    await service.finalize_setup(mailing, AudienceType.ALL, None, scheduled_at=run_at)
    await session.commit()

    assert mailing.status == MailingStatus.SCHEDULED
    assert mailing.scheduled_at is not None

    due = await service.list_due(datetime.now())
    assert mailing.id not in [m.id for m in due]

    due_later = await service.list_due(run_at + timedelta(minutes=1))
    assert mailing.id in [m.id for m in due_later]


async def test_cancel_mailing_sets_cancelled_status(session):
    service = MailingService(FakeBot(), session)
    mailing = await service.create_draft(text="Отмена", photo_file_id=None, created_by=111111)
    await session.commit()

    await service.cancel(mailing)
    await session.commit()

    assert mailing.status == MailingStatus.CANCELLED


async def test_send_now_delivers_to_all_recipients_and_updates_counters(session):
    u1 = await _make_user(session, 6006, subscribed=True)
    u2 = await _make_user(session, 6007, subscribed=True)

    bot = FakeBot()
    service = MailingService(bot, session)
    mailing = await service.create_draft(text="Всем привет!", photo_file_id=None, created_by=111111)
    await session.commit()

    await service.finalize_setup(mailing, AudienceType.ALL, None, scheduled_at=None)
    await session.commit()

    result = await service.send_now(mailing.id)

    assert result.status == MailingStatus.COMPLETED
    assert result.sent == 2
    assert result.failed == 0
    assert result.blocked == 0

    sent_chat_ids = {chat_id for chat_id, _ in bot.sent}
    assert sent_chat_ids == {u1.telegram_id, u2.telegram_id}
    assert all(text == "Всем привет!" for _, text in bot.sent)
