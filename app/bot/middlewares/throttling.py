from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

DEFAULT_THROTTLE_SECONDS = 0.7


class ThrottlingMiddleware(BaseMiddleware):
    """Debounces rapid duplicate button taps / messages per user to prevent double actions."""

    def __init__(self, rate: float = DEFAULT_THROTTLE_SECONDS) -> None:
        self.rate = rate
        self._last_seen: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_id: int | None = None
        if isinstance(event, (CallbackQuery, Message)) and event.from_user:
            user_id = event.from_user.id

        if user_id is not None:
            now = time.monotonic()
            last = self._last_seen.get(user_id, 0.0)
            if now - last < self.rate:
                if isinstance(event, CallbackQuery):
                    await event.answer()
                return None
            self._last_seen[user_id] = now

        return await handler(event, data)
