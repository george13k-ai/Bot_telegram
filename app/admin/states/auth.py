from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminAuth(StatesGroup):
    waiting_for_code = State()
