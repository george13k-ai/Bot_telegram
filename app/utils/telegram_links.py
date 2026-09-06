from __future__ import annotations

import re
from dataclasses import dataclass

# Публичный канал: https://t.me/<username>/<message_id>
_PUBLIC_RE = re.compile(r"^https?://t\.me/([A-Za-z0-9_]{5,})/(\d+)/?(?:\?.*)?$")
# Приватный канал: https://t.me/c/<internal_id>/<message_id>
_PRIVATE_RE = re.compile(r"^https?://t\.me/c/(\d+)/(\d+)/?(?:\?.*)?$")
# Голая ссылка на публичный канал (без поста): https://t.me/<username>
_CHANNEL_RE = re.compile(r"^https?://t\.me/([A-Za-z0-9_]{5,})/?(?:\?.*)?$")
_RESERVED_PATHS = {"c", "joinchat", "share"}


@dataclass(frozen=True)
class TelegramPost:
    message_id: int
    chat_username: str | None = None
    chat_id: int | None = None

    def matches_chat(self, username: str | None, chat_id: int) -> bool:
        if self.chat_username is not None:
            return username is not None and username.lower() == self.chat_username.lower()
        return self.chat_id == chat_id


def parse_post_url(url: str | None) -> TelegramPost | None:
    if not url:
        return None
    url = url.strip()

    match = _PUBLIC_RE.match(url)
    if match:
        username, message_id = match.groups()
        return TelegramPost(message_id=int(message_id), chat_username=username)

    match = _PRIVATE_RE.match(url)
    if match:
        internal_id, message_id = match.groups()
        return TelegramPost(message_id=int(message_id), chat_id=int(f"-100{internal_id}"))

    return None


def parse_channel_username(url: str | None) -> str | None:
    """
    Достаёт username из ссылки на публичный канал (https://t.me/username).
    Для приватных ссылок (t.me/+..., t.me/joinchat/..., t.me/c/...) возвращает
    None - у них нет username, только числовой ID канала, который бот узнать
    из одной лишь ссылки не может.
    """
    if not url:
        return None
    match = _CHANNEL_RE.match(url.strip())
    if not match:
        return None
    username = match.group(1)
    if username.lower() in _RESERVED_PATHS:
        return None
    return username
