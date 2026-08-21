from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callback_data import AdminMenuCB, ContentCB


def subscriptions_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✏️ Текст приглашения подписаться",
            callback_data=ContentCB(action="view", key="subscription_message").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Канал (ссылка/название)", callback_data=AdminMenuCB(section="settings").pack()
        )
    )
    builder.row(InlineKeyboardButton(text="⬅️ В меню админки", callback_data=AdminMenuCB(section="home").pack()))
    return builder.as_markup()
