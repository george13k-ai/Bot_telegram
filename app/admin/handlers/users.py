from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.users import PAGE_SIZE, user_card_keyboard, users_list_keyboard
from app.admin.states.user_search import AdminUserSearch
from app.database.models.support import MessageSender
from app.database.models.user import User
from app.database.repositories.event_repo import EventRepository
from app.services.files import FileService
from app.services.specialist import SpecialistService
from app.services.tags import TagService
from app.services.users import UsersService
from app.utils.callback_data import AdminMenuCB, AdminUserCB
from app.utils.formatting import format_datetime

router = Router(name="admin_users")


async def _render_list(target: Message, session: AsyncSession, page: int) -> None:
    users_service = UsersService(session)
    users = await users_service.list_paginated(limit=PAGE_SIZE + 1, offset=page * PAGE_SIZE)
    has_next = len(users) > PAGE_SIZE
    users = users[:PAGE_SIZE]
    total = await users_service.count_all()
    await target.answer(
        f"Пользователи (всего: {total})", reply_markup=users_list_keyboard(users, page, has_next)
    )


@router.callback_query(AdminMenuCB.filter(F.section == "users"))
async def on_users_section(callback: CallbackQuery, session: AsyncSession) -> None:
    await _render_list(callback.message, session, page=0)
    await callback.answer()


@router.callback_query(AdminUserCB.filter(F.action == "list"))
async def on_users_list(callback: CallbackQuery, session: AsyncSession, callback_data: AdminUserCB) -> None:
    await _render_list(callback.message, session, page=callback_data.page)
    await callback.answer()


@router.callback_query(AdminUserCB.filter(F.action == "search"))
async def on_users_search_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminUserSearch.waiting_for_query)
    await callback.message.answer("Введите username, имя или Telegram ID пользователя для поиска:")
    await callback.answer()


@router.message(AdminUserSearch.waiting_for_query, F.text)
async def on_users_search_query(message: Message, session: AsyncSession, state: FSMContext) -> None:
    users_service = UsersService(session)
    results = await users_service.search(message.text.strip())
    await state.set_state(None)
    if not results:
        await message.answer("Ничего не найдено.")
        return
    await message.answer(
        f"Найдено: {len(results)}", reply_markup=users_list_keyboard(results, page=0, has_next=False)
    )


@router.callback_query(AdminUserCB.filter(F.action == "card"))
async def on_user_card(callback: CallbackQuery, session: AsyncSession, callback_data: AdminUserCB) -> None:
    user = await session.get(User, callback_data.user_id)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    tags_service = TagService(session)
    files_service = FileService(session)
    specialist_service = SpecialistService(session)
    events_repo = EventRepository(session)

    user_tags = await tags_service.list_for_user(user.id)
    all_tags = await tags_service.list_all()
    files = await files_service.list_for_user(user.id)
    tickets = await specialist_service.list_for_user(user.id)
    messages = await specialist_service.list_recent_messages_for_user(user.id, limit=5)
    events = await events_repo.list_for_user(user.id, limit=8)

    lines = [
        f"<b>Карточка пользователя #{user.id}</b>",
        "",
        f"Telegram ID: <code>{user.telegram_id}</code>",
        f"Username: {('@' + user.username) if user.username else '—'}",
        f"Имя: {' '.join(filter(None, [user.first_name, user.last_name])) or '—'}",
        f"Регистрация: {format_datetime(user.created_at)}",
        f"Последняя активность: {format_datetime(user.last_activity_at)}",
        f"Подписка: {'✅' if user.is_subscribed else '❌'}",
        f"Заблокировал бота: {'да' if user.is_blocked else 'нет'}",
        f"Теги: {', '.join('#' + t.name for t in user_tags) or '—'}",
    ]

    lines.append("")
    lines.append(f"<b>Файлы</b> ({len(files)}):")
    if files:
        for f in files[:5]:
            lines.append(f"  • {f.file_name or f.telegram_file_id} — {format_datetime(f.created_at)}")
    else:
        lines.append("  —")

    lines.append("")
    lines.append(f"<b>Заявки</b> ({len(tickets)}):")
    if tickets:
        for ticket in tickets[:5]:
            lines.append(f"  • #{ticket.id} [{ticket.status_label}] от {format_datetime(ticket.created_at)}")
    else:
        lines.append("  —")

    lines.append("")
    lines.append("<b>История сообщений</b>:")
    if messages:
        for m in messages:
            who = "Админ" if m.sender == MessageSender.ADMIN else "Пользователь"
            snippet = (m.text or "")[:80]
            lines.append(f"  • {format_datetime(m.created_at)} [{who}]: {snippet}")
    else:
        lines.append("  —")

    lines.append("")
    lines.append("<b>История взаимодействия</b>:")
    if events:
        for e in events:
            lines.append(f"  • {format_datetime(e.created_at)} — {e.event_type.value}")
    else:
        lines.append("  —")

    await callback.message.answer(
        "\n".join(lines), reply_markup=user_card_keyboard(user.id, user_tags, all_tags)
    )
    await callback.answer()


@router.callback_query(AdminUserCB.filter(F.action == "tag_add"))
async def on_tag_add(callback: CallbackQuery, session: AsyncSession, callback_data: AdminUserCB) -> None:
    tags_service = TagService(session)
    tag = await tags_service.get_by_id(callback_data.tag_id)
    if tag is not None:
        await tags_service.repo.assign(callback_data.user_id, tag.id)
    await on_user_card(callback, session, AdminUserCB(action="card", user_id=callback_data.user_id))


@router.callback_query(AdminUserCB.filter(F.action == "tag_remove"))
async def on_tag_remove(callback: CallbackQuery, session: AsyncSession, callback_data: AdminUserCB) -> None:
    tags_service = TagService(session)
    tag = await tags_service.get_by_id(callback_data.tag_id)
    if tag is not None:
        await tags_service.repo.remove(callback_data.user_id, tag.id)
    await on_user_card(callback, session, AdminUserCB(action="card", user_id=callback_data.user_id))
