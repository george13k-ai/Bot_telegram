from __future__ import annotations

from app.database.models.mailing import AudienceType
from app.services.mailings import MailingService
from app.services.tags import TAG_PRO, TagService
from app.services.users import UsersService


class FakeBot:
    pass


async def _make_user(session, telegram_id: int):
    users = UsersService(session)
    user, _ = await users.get_or_create(telegram_id=telegram_id, username=None, first_name="U", last_name=None)
    await session.commit()
    return user


async def test_tag_assignment_and_lookup(session):
    user = await _make_user(session, 7001)
    tags = TagService(session)

    await tags.mark_pro(user.id)
    await session.commit()

    user_tags = await tags.list_for_user(user.id)
    assert any(t.name == TAG_PRO for t in user_tags)


async def test_mailing_audience_filters_by_tag(session):
    tagged_user = await _make_user(session, 7002)
    other_user = await _make_user(session, 7003)

    tags = TagService(session)
    await tags.mark_pro(tagged_user.id)
    await session.commit()

    pro_tag = next(t for t in await tags.list_all() if t.name == TAG_PRO)

    mailing_service = MailingService(FakeBot(), session)
    audience = await mailing_service.build_audience(AudienceType.TAG, {"tag_id": pro_tag.id})

    audience_ids = {u.id for u in audience}
    assert tagged_user.id in audience_ids
    assert other_user.id not in audience_ids


async def test_assign_is_idempotent(session):
    user = await _make_user(session, 7004)
    tags = TagService(session)

    await tags.mark_pro(user.id)
    await tags.mark_pro(user.id)
    await session.commit()

    user_tags = await tags.list_for_user(user.id)
    pro_tags = [t for t in user_tags if t.name == TAG_PRO]
    assert len(pro_tags) == 1
