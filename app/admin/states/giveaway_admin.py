from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class GiveawayAdminForm(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_image = State()
