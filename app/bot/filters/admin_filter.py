from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from app.config import settings


class IsAdminFilter(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return user.id in settings.admin_ids
