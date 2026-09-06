from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.services.content import ContentService
from app.services.subscriptions import SubscriptionService
from app.services.users import UsersService


@dataclass
class FakeMember:
    status: str


class FakeBot:
    def __init__(self, status: str) -> None:
        self.status = status
        self.calls: list[tuple[int, int]] = []

    async def get_chat_member(self, chat_id: int, user_id: int) -> FakeMember:
        self.calls.append((chat_id, user_id))
        return FakeMember(status=self.status)


@pytest.mark.parametrize("status", ["member", "administrator", "creator"])
async def test_active_statuses_count_as_subscribed(session, status):
    bot = FakeBot(status)
    service = SubscriptionService(bot, session)
    assert await service.is_subscribed(12345) is True


@pytest.mark.parametrize("status", ["left", "kicked", "restricted"])
async def test_inactive_statuses_are_not_subscribed(session, status):
    bot = FakeBot(status)
    service = SubscriptionService(bot, session)
    assert await service.is_subscribed(12345) is False


async def test_join_request_counts_as_subscribed_when_approval_required(session):
    users = UsersService(session)
    user, _ = await users.get_or_create(telegram_id=999, username=None, first_name="U", last_name=None)
    await users.set_channel_join_requested(user)
    await session.commit()

    content = ContentService(session)
    await content.set_require_join_approval(True, updated_by=1)
    await session.commit()

    bot = FakeBot("left")  # not an actual member yet - request is still pending approval
    service = SubscriptionService(bot, session)
    assert await service.is_subscribed(999) is True


async def test_join_request_ignored_when_approval_setting_disabled(session):
    users = UsersService(session)
    user, _ = await users.get_or_create(telegram_id=998, username=None, first_name="U", last_name=None)
    await users.set_channel_join_requested(user)
    await session.commit()

    bot = FakeBot("left")
    service = SubscriptionService(bot, session)
    assert await service.is_subscribed(998) is False


async def test_pending_join_request_without_setting_user_row_is_not_subscribed(session):
    content = ContentService(session)
    await content.set_require_join_approval(True, updated_by=1)
    await session.commit()

    bot = FakeBot("left")
    service = SubscriptionService(bot, session)
    # No user row exists at all for this telegram_id.
    assert await service.is_subscribed(123456789) is False
