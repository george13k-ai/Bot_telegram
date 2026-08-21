from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models.mailing import Mailing
from app.database.models.tag import Tag
from app.utils.callback_data import AdminMenuCB, MailingCB


def mailings_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Все рассылки", callback_data=MailingCB(action="list").pack()))
    builder.row(InlineKeyboardButton(text="➕ Добавить рассылку", callback_data=MailingCB(action="create").pack()))
    builder.row(InlineKeyboardButton(text="⬅️ В меню админки", callback_data=AdminMenuCB(section="home").pack()))
    return builder.as_markup()


def photo_choice_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Добавить фото", callback_data=MailingCB(action="add_photo").pack()))
    builder.row(InlineKeyboardButton(text="Без фото", callback_data=MailingCB(action="no_photo").pack()))
    return builder.as_markup()


def preview_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Уверен", callback_data=MailingCB(action="preview_ok").pack()),
        InlineKeyboardButton(text="Нет", callback_data=MailingCB(action="preview_no").pack()),
    )
    return builder.as_markup()


def audience_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Все пользователи", callback_data=MailingCB(action="audience_all").pack()))
    builder.row(
        InlineKeyboardButton(text="Активированные", callback_data=MailingCB(action="audience_activated").pack())
    )
    builder.row(InlineKeyboardButton(text="По тегу", callback_data=MailingCB(action="audience_tag").pack()))
    builder.row(
        InlineKeyboardButton(text="Отправившие файл", callback_data=MailingCB(action="audience_file_sent").pack())
    )
    return builder.as_markup()


def audience_tag_keyboard(tags: list[Tag]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tag in tags:
        builder.row(
            InlineKeyboardButton(
                text=f"#{tag.name}",
                callback_data=MailingCB(action="audience_tag_pick", tag_id=tag.id).pack(),
            )
        )
    return builder.as_markup()


def time_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Сейчас", callback_data=MailingCB(action="time_now").pack()))
    builder.row(InlineKeyboardButton(text="Через 2 часа", callback_data=MailingCB(action="time_2h").pack()))
    builder.row(InlineKeyboardButton(text="Другое время", callback_data=MailingCB(action="time_custom").pack()))
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Подтвердить", callback_data=MailingCB(action="confirm").pack()),
        InlineKeyboardButton(text="Отменить", callback_data=MailingCB(action="cancel_draft").pack()),
    )
    return builder.as_markup()


def mailings_list_keyboard(mailings: list[Mailing], page: int, has_next: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for mailing in mailings:
        label = f"#{mailing.id} [{mailing.status.value}] {mailing.text[:20]}"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=MailingCB(action="view", mailing_id=mailing.id).pack())
        )
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=MailingCB(action="list", page=page - 1).pack()))
    if has_next:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=MailingCB(action="list", page=page + 1).pack()))
    if nav_row:
        builder.row(*nav_row)
    builder.row(InlineKeyboardButton(text="⬅️ К рассылкам", callback_data=MailingCB(action="menu").pack()))
    return builder.as_markup()


def mailing_detail_keyboard(mailing: Mailing) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    from app.database.models.mailing import MailingStatus

    if mailing.status == MailingStatus.SCHEDULED:
        builder.row(
            InlineKeyboardButton(text="Отменить", callback_data=MailingCB(action="cancel", mailing_id=mailing.id).pack())
        )
    builder.row(InlineKeyboardButton(text="⬅️ К списку", callback_data=MailingCB(action="list").pack()))
    return builder.as_markup()
