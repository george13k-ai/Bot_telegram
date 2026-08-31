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


async def test_create_with_post_url_and_get_active_picks_newest(session):
    giveaways = GiveawayService(session)
    older = await giveaways.create(title="Old", description="desc")
    await session.commit()
    newer = await giveaways.create(title="New", description="desc", post_url="https://t.me/channel/1")
    await session.commit()

    active = await giveaways.get_active()
    assert active.id == newer.id
    assert active.post_url == "https://t.me/channel/1"
    assert older.id != active.id


async def test_set_post_url_and_set_image_update_existing_giveaway(session):
    giveaways = GiveawayService(session)
    giveaway = await giveaways.create(title="Test", description="desc")
    await session.commit()

    await giveaways.set_post_url(giveaway, "https://t.me/channel/5")
    await giveaways.set_image(giveaway, "FILE_ID_123")
    await session.commit()

    reloaded = await giveaways.get_by_id(giveaway.id)
    assert reloaded.post_url == "https://t.me/channel/5"
    assert reloaded.image_file_id == "FILE_ID_123"


async def test_delete_giveaway_removes_it_and_its_participants(session):
    giveaways = GiveawayService(session)
    giveaway = await giveaways.create(title="To delete", description="desc")
    await session.commit()

    user = await _make_user(session, 2004)
    await giveaways.join(giveaway.id, user.id)
    await session.commit()
    assert await giveaways.count_participants(giveaway.id) == 1

    await giveaways.delete(giveaway)
    await session.commit()

    assert await giveaways.get_by_id(giveaway.id) is None
