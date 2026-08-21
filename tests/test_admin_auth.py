from __future__ import annotations

from dataclasses import dataclass

from app.bot.filters.admin_filter import IsAdminFilter
from app.config import settings


@dataclass
class FakeUser:
    id: int


@dataclass
class FakeEvent:
    from_user: FakeUser | None


async def test_admin_id_passes_filter():
    admin_id = next(iter(settings.admin_ids))
    filter_ = IsAdminFilter()
    assert await filter_(FakeEvent(from_user=FakeUser(id=admin_id))) is True


async def test_non_admin_id_rejected():
    filter_ = IsAdminFilter()
    assert await filter_(FakeEvent(from_user=FakeUser(id=999999999))) is False


async def test_event_without_user_rejected():
    filter_ = IsAdminFilter()
    assert await filter_(FakeEvent(from_user=None)) is False
