from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.callback_data import AdminMenuCB

SECTIONS: list[tuple[str, str]] = [
    ("Пользователи", "users"),
    ("Рассылки", "mailings"),
    ("Розыгрыши", "giveaways"),
    ("Подписки", "subscriptions"),
    ("Уведомления", "notifications"),
    ("Статистика", "statistics"),
    ("Контент", "content"),
    ("Настройки", "settings"),
]


def admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for title, section in SECTIONS:
        builder.row(InlineKeyboardButton(text=title, callback_data=AdminMenuCB(section=section).pack()))
    return builder.as_markup()


def back_to_admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ В меню админки", callback_data=AdminMenuCB(section="home").pack()))
    return builder.as_markup()
