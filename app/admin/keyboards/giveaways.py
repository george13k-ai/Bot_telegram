from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.giveaway import Giveaway
from app.utils.callback_data import AdminMenuCB, GiveawayAdminCB


def giveaways_list_keyboard(giveaways: list[Giveaway], page: int, has_next: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for giveaway in giveaways:
        state = "🟢" if giveaway.is_active else "⚪️"
        builder.row(
            InlineKeyboardButton(
                text=f"{state} {giveaway.title}",
                callback_data=GiveawayAdminCB(action="view", giveaway_id=giveaway.id).pack(),
            )
        )
    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="◀️", callback_data=GiveawayAdminCB(action="list", page=page - 1).pack())
        )
    if has_next:
        nav_row.append(
            InlineKeyboardButton(text="▶️", callback_data=GiveawayAdminCB(action="list", page=page + 1).pack())
        )
    if nav_row:
        builder.row(*nav_row)
    builder.row(InlineKeyboardButton(text="➕ Добавить розыгрыш", callback_data=GiveawayAdminCB(action="create").pack()))
    builder.row(InlineKeyboardButton(text="⬅️ В меню админки", callback_data=AdminMenuCB(section="home").pack()))
    return builder.as_markup()


def giveaway_detail_keyboard(giveaway: Giveaway) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    toggle_text = "🔴 Деактивировать" if giveaway.is_active else "🟢 Активировать"
    builder.row(
        InlineKeyboardButton(
            text=toggle_text, callback_data=GiveawayAdminCB(action="toggle", giveaway_id=giveaway.id).pack()
        )
    )
    photo_text = "🖼 Изменить фото" if giveaway.image_file_id else "🖼 Добавить фото"
    builder.row(
        InlineKeyboardButton(
            text=photo_text, callback_data=GiveawayAdminCB(action="set_photo", giveaway_id=giveaway.id).pack()
        )
    )
    link_text = "🔗 Изменить ссылку на пост" if giveaway.post_url else "🔗 Добавить ссылку на пост"
    builder.row(
        InlineKeyboardButton(
            text=link_text, callback_data=GiveawayAdminCB(action="set_post_url", giveaway_id=giveaway.id).pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить розыгрыш", callback_data=GiveawayAdminCB(action="delete", giveaway_id=giveaway.id).pack()
        )
    )
    builder.row(InlineKeyboardButton(text="⬅️ К списку", callback_data=GiveawayAdminCB(action="list").pack()))
    return builder.as_markup()


def giveaway_delete_confirm_keyboard(giveaway: Giveaway) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=GiveawayAdminCB(action="delete_confirm", giveaway_id=giveaway.id).pack(),
        ),
        InlineKeyboardButton(
            text="❌ Отмена", callback_data=GiveawayAdminCB(action="view", giveaway_id=giveaway.id).pack()
        ),
    )
    return builder.as_markup()


def giveaway_post_url_skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Пропустить", callback_data=GiveawayAdminCB(action="post_url_skip").pack()))
    return builder.as_markup()
