from __future__ import annotations

from app.services.content import ContentService


async def test_get_channel_id_falls_back_to_env_default(session):
    content = ContentService(session)
    # Before seeding, no row exists yet -> falls back to settings.REQUIRED_CHANNEL_ID
    channel_id = await content.get_channel_id()
    assert isinstance(channel_id, int)


async def test_set_channel_url_auto_derives_username_for_public_channel(session):
    content = ContentService(session)
    username = await content.set_channel_url("https://t.me/new_channel", updated_by=1)
    await session.commit()

    assert username == "new_channel"
    assert await content.get_channel_url() == "https://t.me/new_channel"
    assert await content.get_channel_id() == "@new_channel"


async def test_set_channel_url_leaves_channel_id_untouched_for_private_link(session):
    content = ContentService(session)
    await content.set_channel_id(-1009999999999, updated_by=1)
    await session.commit()

    username = await content.set_channel_url("https://t.me/+privateInviteHash", updated_by=1)
    await session.commit()

    assert username is None
    assert await content.get_channel_url() == "https://t.me/+privateInviteHash"
    assert await content.get_channel_id() == -1009999999999


async def test_require_join_approval_default_false_and_toggle(session):
    content = ContentService(session)
    assert await content.get_require_join_approval() is False

    await content.set_require_join_approval(True, updated_by=1)
    await session.commit()
    assert await content.get_require_join_approval() is True

    await content.set_require_join_approval(False, updated_by=1)
    await session.commit()
    assert await content.get_require_join_approval() is False


async def test_unsubscribe_reminder_minutes_default_and_custom(session):
    content = ContentService(session)
    assert await content.get_unsubscribe_reminder_minutes() == 30

    await content.set_text("setting_unsubscribe_reminder_minutes", "45", updated_by=1)
    await session.commit()
    assert await content.get_unsubscribe_reminder_minutes() == 45


async def test_unsubscribe_reminder_minutes_ignores_garbage_input(session):
    content = ContentService(session)
    await content.set_text("setting_unsubscribe_reminder_minutes", "not-a-number", updated_by=1)
    await session.commit()
    assert await content.get_unsubscribe_reminder_minutes() == 30

    await content.set_text("setting_unsubscribe_reminder_minutes", "-5", updated_by=1)
    await session.commit()
    assert await content.get_unsubscribe_reminder_minutes() == 30
