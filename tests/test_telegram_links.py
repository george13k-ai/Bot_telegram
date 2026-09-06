from __future__ import annotations

from app.utils.telegram_links import parse_channel_username, parse_post_url


def test_parse_public_channel_url():
    post = parse_post_url("https://t.me/strah_bankira/170")
    assert post is not None
    assert post.message_id == 170
    assert post.chat_username == "strah_bankira"
    assert post.chat_id is None


def test_parse_private_channel_url():
    post = parse_post_url("https://t.me/c/1234567890/42")
    assert post is not None
    assert post.message_id == 42
    assert post.chat_id == -1001234567890
    assert post.chat_username is None


def test_parse_invalid_url_returns_none():
    assert parse_post_url("https://example.com/not-telegram") is None
    assert parse_post_url("not a url at all") is None
    assert parse_post_url(None) is None
    assert parse_post_url("") is None


def test_matches_chat_for_public_channel_is_case_insensitive():
    post = parse_post_url("https://t.me/strah_bankira/170")
    assert post.matches_chat("Strah_Bankira", chat_id=999) is True
    assert post.matches_chat("other_channel", chat_id=999) is False
    assert post.matches_chat(None, chat_id=999) is False


def test_matches_chat_for_private_channel_uses_chat_id():
    post = parse_post_url("https://t.me/c/1234567890/42")
    assert post.matches_chat(username=None, chat_id=-1001234567890) is True
    assert post.matches_chat(username=None, chat_id=-1009999999999) is False


def test_parse_ignores_query_string_and_trailing_slash():
    post = parse_post_url("https://t.me/strah_bankira/170/?single")
    assert post is not None
    assert post.message_id == 170
    assert post.chat_username == "strah_bankira"


def test_parse_channel_username_from_bare_public_link():
    assert parse_channel_username("https://t.me/strah_bankira") == "strah_bankira"
    assert parse_channel_username("https://t.me/strah_bankira/") == "strah_bankira"


def test_parse_channel_username_rejects_private_links():
    assert parse_channel_username("https://t.me/+AbCdEfGh12345") is None
    assert parse_channel_username("https://t.me/joinchat/AbCdEfGh12345") is None
    assert parse_channel_username("https://t.me/c/1234567890") is None
    assert parse_channel_username(None) is None
    assert parse_channel_username("") is None


def test_parse_channel_username_rejects_post_links():
    # A link to a specific post is not "the channel itself" for this helper -
    # callers that need the post should use parse_post_url instead.
    assert parse_channel_username("https://t.me/strah_bankira/170") is None
