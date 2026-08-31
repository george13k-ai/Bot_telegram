from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class GiveawayAdminForm(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_image = State()
    waiting_for_post_url = State()
    waiting_for_image_edit = State()
    waiting_for_post_url_edit = State()
