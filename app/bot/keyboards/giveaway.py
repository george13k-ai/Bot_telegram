from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.common import home_button


def giveaway_intro_keyboard(channel_url: str, post_url: str | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Подписаться на канал", url=channel_url))
    if post_url:
        builder.row(InlineKeyboardButton(text="Открыть пост", url=post_url))
    builder.row(home_button())
    return builder.as_markup()
