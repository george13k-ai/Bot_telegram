from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.content import Content
from app.services.content import SETTINGS_KEYS, content_label
from app.utils.callback_data import AdminMenuCB, ContentCB

# Настройки-переключатели (да/нет) - удобнее менять кнопкой, чем текстом.
BOOLEAN_SETTING_KEYS = {"setting_require_join_approval"}


def content_list_keyboard(items: list[Content]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.row(
            InlineKeyboardButton(text=content_label(item.key), callback_data=ContentCB(action="view", key=item.key).pack())
        )
    builder.row(InlineKeyboardButton(text="⬅️ В меню админки", callback_data=AdminMenuCB(section="home").pack()))
    return builder.as_markup()


def content_detail_keyboard(key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if key in BOOLEAN_SETTING_KEYS:
        builder.row(
            InlineKeyboardButton(text="🔁 Переключить", callback_data=ContentCB(action="toggle_bool", key=key).pack())
        )
    else:
        builder.row(
            InlineKeyboardButton(text="✏️ Изменить текст", callback_data=ContentCB(action="edit_text", key=key).pack())
        )
        if key not in SETTINGS_KEYS:
            builder.row(
                InlineKeyboardButton(text="🖼 Изменить медиа", callback_data=ContentCB(action="edit_media", key=key).pack())
            )
    builder.row(InlineKeyboardButton(text="⬅️ К списку", callback_data=ContentCB(action="list").pack()))
    return builder.as_markup()
