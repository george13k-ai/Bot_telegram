from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callback_data import MainCB, SpecialistCB


def specialist_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="Написать специалисту", callback_data=SpecialistCB(action="create").pack()
    )


def home_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(text="На главную", callback_data=MainCB(action="home").pack())


def with_home(builder: InlineKeyboardBuilder) -> InlineKeyboardMarkup:
    builder.row(home_button())
    return builder.as_markup()


def with_specialist_and_home(builder: InlineKeyboardBuilder | None = None) -> InlineKeyboardMarkup:
    builder = builder or InlineKeyboardBuilder()
    builder.row(specialist_button())
    builder.row(home_button())
    return builder.as_markup()


def specialist_only_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    return with_specialist_and_home(builder)
