from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.database.models.giveaway import GiveawayParticipant
from app.services.giveaway import GiveawayService
from app.services.users import UsersService


async def _make_user(session, telegram_id: int):
    users = UsersService(session)
    user, _ = await users.get_or_create(telegram_id=telegram_id, username=None, first_name="U", last_name=None)
    await session.commit()
    return user


async def test_join_giveaway_success(session):
    giveaways = GiveawayService(session)
    giveaway = await giveaways.create(title="Test giveaway", description="desc")
    await session.commit()

    user = await _make_user(session, 2001)

    result = await giveaways.join(giveaway.id, user.id)
    await session.commit()

    assert result.joined is True
    assert result.already_participant is False
    assert await giveaways.count_participants(giveaway.id) == 1


async def test_join_giveaway_twice_is_rejected(session):
    giveaways = GiveawayService(session)
    giveaway = await giveaways.create(title="Test giveaway", description="desc")
    await session.commit()

    user = await _make_user(session, 2002)

    first = await giveaways.join(giveaway.id, user.id)
    await session.commit()
    second = await giveaways.join(giveaway.id, user.id)
    await session.commit()

    assert first.joined is True
    assert second.joined is False
    assert second.already_participant is True
    assert await giveaways.count_participants(giveaway.id) == 1


async def test_unique_constraint_enforced_at_db_level(session):
    """Defense in depth: even bypassing the service pre-check, the DB rejects duplicates."""
    giveaways = GiveawayService(session)
    giveaway = await giveaways.create(title="Test giveaway", description="desc")
    await session.commit()

    user = await _make_user(session, 2003)

    session.add(GiveawayParticipant(giveaway_id=giveaway.id, user_id=user.id))
    await session.commit()

    session.add(GiveawayParticipant(giveaway_id=giveaway.id, user_id=user.id))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
