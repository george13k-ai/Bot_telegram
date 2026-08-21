from __future__ import annotations

from app.services.tags import TAG_NEWBIE
from app.services.users import UsersService


async def test_get_or_create_creates_new_user(session):
    service = UsersService(session)
    user, is_new = await service.get_or_create(
        telegram_id=1001, username="john", first_name="John", last_name="Doe"
    )
    await session.commit()

    assert is_new is True
    assert user.telegram_id == 1001
    assert user.username == "john"


async def test_get_or_create_returns_existing_user_and_updates_activity(session):
    service = UsersService(session)
    user, _ = await service.get_or_create(telegram_id=1002, username="old_name", first_name="A", last_name=None)
    await session.commit()

    same_user, is_new = await service.get_or_create(
        telegram_id=1002, username="new_name", first_name="A", last_name=None
    )
    await session.commit()

    assert is_new is False
    assert same_user.id == user.id
    assert same_user.username == "new_name"


async def test_register_start_assigns_newbie_tag(session):
    service = UsersService(session)
    user, _ = await service.get_or_create(telegram_id=1003, username="newbie", first_name="N", last_name=None)
    await session.commit()

    await service.register_start(user)
    await session.commit()

    tags = await service.tags.list_for_user(user.id)
    assert any(t.name == TAG_NEWBIE for t in tags)


async def test_unblocked_on_repeat_start(session):
    service = UsersService(session)
    user, _ = await service.get_or_create(telegram_id=1004, username="u", first_name="U", last_name=None)
    await service.block(user)
    await session.commit()
    assert user.is_blocked is True

    user_again, is_new = await service.get_or_create(telegram_id=1004, username="u", first_name="U", last_name=None)
    await session.commit()

    assert is_new is False
    assert user_again.is_blocked is False
