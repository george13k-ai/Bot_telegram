from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.services.subscriptions import SubscriptionService


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
async def test_active_statuses_count_as_subscribed(status):
    bot = FakeBot(status)
    service = SubscriptionService(bot)
    assert await service.is_subscribed(12345) is True


@pytest.mark.parametrize("status", ["left", "kicked", "restricted"])
async def test_inactive_statuses_are_not_subscribed(status):
    bot = FakeBot(status)
    service = SubscriptionService(bot)
    assert await service.is_subscribed(12345) is False
