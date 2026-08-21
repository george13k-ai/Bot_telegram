from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminReply(StatesGroup):
    waiting_for_reply = State()
