from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callback_data import MainCB


def start_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Да", callback_data=MainCB(action="yes").pack()))
    builder.row(InlineKeyboardButton(text="Розыгрыш", callback_data=MainCB(action="giveaway").pack()))
    builder.row(
        InlineKeyboardButton(text="Написать специалисту", callback_data=MainCB(action="specialist").pack())
    )
    return builder.as_markup()
