from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class MailingCreate(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()
    waiting_for_custom_time = State()
