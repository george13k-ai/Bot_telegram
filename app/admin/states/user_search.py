from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminUserSearch(StatesGroup):
    waiting_for_query = State()
