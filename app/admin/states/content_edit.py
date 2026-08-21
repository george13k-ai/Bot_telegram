from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ContentEdit(StatesGroup):
    waiting_for_text = State()
    waiting_for_media = State()
