from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards.common import home_button
from app.utils.callback_data import SubscriptionCB


def subscription_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Перейти к каналу", url=channel_url))
    builder.row(
        InlineKeyboardButton(text="Проверить подписку", callback_data=SubscriptionCB(action="check").pack())
    )
    builder.row(home_button())
    return builder.as_markup()
