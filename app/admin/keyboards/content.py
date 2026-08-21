from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.content import Content
from app.utils.callback_data import AdminMenuCB, ContentCB


def content_list_keyboard(items: list[Content]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.row(InlineKeyboardButton(text=item.key, callback_data=ContentCB(action="view", key=item.key).pack()))
    builder.row(InlineKeyboardButton(text="⬅️ В меню админки", callback_data=AdminMenuCB(section="home").pack()))
    return builder.as_markup()


def content_detail_keyboard(key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Изменить текст", callback_data=ContentCB(action="edit_text", key=key).pack()))
    builder.row(InlineKeyboardButton(text="🖼 Изменить медиа", callback_data=ContentCB(action="edit_media", key=key).pack()))
    builder.row(InlineKeyboardButton(text="⬅️ К списку", callback_data=ContentCB(action="list").pack()))
    return builder.as_markup()
