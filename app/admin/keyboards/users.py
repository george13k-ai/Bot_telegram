from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.tag import Tag
from app.database.models.user import User
from app.utils.callback_data import AdminMenuCB, AdminUserCB

PAGE_SIZE = 10


def users_list_keyboard(users: list[User], page: int, has_next: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for user in users:
        label = f"#{user.id} {user.display_name}"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=AdminUserCB(action="card", user_id=user.id).pack())
        )

    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="◀️", callback_data=AdminUserCB(action="list", page=page - 1).pack())
        )
    if has_next:
        nav_row.append(
            InlineKeyboardButton(text="▶️", callback_data=AdminUserCB(action="list", page=page + 1).pack())
        )
    if nav_row:
        builder.row(*nav_row)

    builder.row(InlineKeyboardButton(text="🔎 Поиск", callback_data=AdminUserCB(action="search").pack()))
    builder.row(InlineKeyboardButton(text="⬅️ В меню админки", callback_data=AdminMenuCB(section="home").pack()))
    return builder.as_markup()


def user_card_keyboard(user_id: int, user_tags: list[Tag], all_tags: list[Tag]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    user_tag_ids = {t.id for t in user_tags}
    for tag in all_tags:
        marker = "➖" if tag.id in user_tag_ids else "➕"
        action = "tag_remove" if tag.id in user_tag_ids else "tag_add"
        builder.row(
            InlineKeyboardButton(
                text=f"{marker} {tag.name}",
                callback_data=AdminUserCB(action=action, user_id=user_id, tag_id=tag.id).pack(),
            )
        )
    builder.row(InlineKeyboardButton(text="⬅️ К списку пользователей", callback_data=AdminUserCB(action="list").pack()))
    return builder.as_markup()
