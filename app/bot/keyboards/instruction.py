from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.common import home_button, specialist_button
from app.utils.callback_data import InstructionCB


def why_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Получить инструкцию", callback_data=InstructionCB(action="get").pack()))
    builder.row(specialist_button())
    builder.row(home_button())
    return builder.as_markup()
