from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.common import home_button
from app.utils.callback_data import GiveawayCB


def giveaway_intro_keyboard(giveaway_id: int, channel_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Подписаться на канал", url=channel_url))
    builder.row(
        InlineKeyboardButton(
            text="Отправить пост", callback_data=GiveawayCB(action="post", giveaway_id=giveaway_id).pack()
        )
    )
    builder.row(home_button())
    return builder.as_markup()


def giveaway_post_keyboard(giveaway_id: int, giveaway_post_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if giveaway_post_url:
        builder.row(InlineKeyboardButton(text="Открыть пост", url=giveaway_post_url))
    builder.row(
        InlineKeyboardButton(
            text="Участвовать", callback_data=GiveawayCB(action="join", giveaway_id=giveaway_id).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Назад", callback_data=GiveawayCB(action="open", giveaway_id=giveaway_id).pack()
        )
    )
    builder.row(home_button())
    return builder.as_markup()


def giveaway_result_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(home_button())
    return builder.as_markup()
