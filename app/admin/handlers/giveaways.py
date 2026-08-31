from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.giveaways import (
    giveaway_delete_confirm_keyboard,
    giveaway_detail_keyboard,
    giveaway_post_url_skip_keyboard,
    giveaways_list_keyboard,
)
from app.admin.states.giveaway_admin import GiveawayAdminForm
from app.services.giveaway import GiveawayService
from app.utils.callback_data import AdminMenuCB, GiveawayAdminCB
from app.utils.formatting import format_datetime

router = Router(name="admin_giveaways")

PAGE_SIZE = 10


def _skip_image_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Без фото", callback_data=GiveawayAdminCB(action="img_skip").pack())
    )
    return builder.as_markup()


async def _render_list(target: Message, session: AsyncSession, page: int) -> None:
    service = GiveawayService(session)
    giveaways = await service.list_all(limit=PAGE_SIZE + 1, offset=page * PAGE_SIZE)
    has_next = len(giveaways) > PAGE_SIZE
    giveaways = giveaways[:PAGE_SIZE]
    await target.answer("<b>Розыгрыши</b>", reply_markup=giveaways_list_keyboard(giveaways, page, has_next))


def _detail_text(giveaway, participants: int) -> str:
    return (
        f"<b>{giveaway.title}</b>\n\n"
        f"{giveaway.description or ''}\n\n"
        f"Активен: {'да' if giveaway.is_active else 'нет'}\n"
        f"Фото: {'есть' if giveaway.image_file_id else 'нет'}\n"
        f"Ссылка на пост: {giveaway.post_url or '—'}\n"
        f"Создан: {format_datetime(giveaway.created_at)}\n"
        f"Участников: {participants}"
    )


@router.callback_query(AdminMenuCB.filter(F.section == "giveaways"))
async def on_giveaways_section(callback: CallbackQuery, session: AsyncSession) -> None:
    await _render_list(callback.message, session, page=0)
    await callback.answer()


@router.callback_query(GiveawayAdminCB.filter(F.action == "list"))
async def on_giveaways_list(callback: CallbackQuery, session: AsyncSession, callback_data: GiveawayAdminCB) -> None:
    await _render_list(callback.message, session, page=callback_data.page)
    await callback.answer()


@router.callback_query(GiveawayAdminCB.filter(F.action == "view"))
async def on_giveaway_view(callback: CallbackQuery, session: AsyncSession, callback_data: GiveawayAdminCB) -> None:
    service = GiveawayService(session)
    giveaway = await service.get_by_id(callback_data.giveaway_id)
    if giveaway is None:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    participants = await service.count_participants(giveaway.id)
    await callback.message.answer(_detail_text(giveaway, participants), reply_markup=giveaway_detail_keyboard(giveaway))
    await callback.answer()


@router.callback_query(GiveawayAdminCB.filter(F.action == "toggle"))
async def on_giveaway_toggle(callback: CallbackQuery, session: AsyncSession, callback_data: GiveawayAdminCB) -> None:
    service = GiveawayService(session)
    giveaway = await service.get_by_id(callback_data.giveaway_id)
    if giveaway is None:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    await service.set_active(giveaway, not giveaway.is_active)
    await on_giveaway_view(callback, session, GiveawayAdminCB(action="view", giveaway_id=giveaway.id))


# --- delete ---


@router.callback_query(GiveawayAdminCB.filter(F.action == "delete"))
async def on_giveaway_delete_confirm(
    callback: CallbackQuery, session: AsyncSession, callback_data: GiveawayAdminCB
) -> None:
    service = GiveawayService(session)
    giveaway = await service.get_by_id(callback_data.giveaway_id)
    if giveaway is None:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    participants = await service.count_participants(giveaway.id)
    warning = f"\n\n⚠️ У розыгрыша {participants} участник(ов) — они тоже будут удалены." if participants else ""
    await callback.message.answer(
        f"Удалить розыгрыш «{giveaway.title}»?{warning}", reply_markup=giveaway_delete_confirm_keyboard(giveaway)
    )
    await callback.answer()


@router.callback_query(GiveawayAdminCB.filter(F.action == "delete_confirm"))
async def on_giveaway_delete(callback: CallbackQuery, session: AsyncSession, callback_data: GiveawayAdminCB) -> None:
    service = GiveawayService(session)
    giveaway = await service.get_by_id(callback_data.giveaway_id)
    if giveaway is None:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    title = giveaway.title
    await service.delete(giveaway)
    await callback.message.answer(f"Розыгрыш «{title}» удалён 🗑")
    await _render_list(callback.message, session, page=0)
    await callback.answer()


# --- edit photo (existing giveaway) ---


@router.callback_query(GiveawayAdminCB.filter(F.action == "set_photo"))
async def on_giveaway_set_photo_start(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext, callback_data: GiveawayAdminCB
) -> None:
    service = GiveawayService(session)
    giveaway = await service.get_by_id(callback_data.giveaway_id)
    if giveaway is None:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    await state.update_data(giveaway_id=giveaway.id)
    await state.set_state(GiveawayAdminForm.waiting_for_image_edit)
    await callback.message.answer(f"Отправьте новое фото для розыгрыша «{giveaway.title}»:")
    await callback.answer()


@router.message(GiveawayAdminForm.waiting_for_image_edit, F.photo)
async def on_giveaway_set_photo(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    await state.set_state(None)

    service = GiveawayService(session)
    giveaway = await service.get_by_id(giveaway_id) if giveaway_id else None
    if giveaway is None:
        await message.answer("Розыгрыш не найден.")
        return

    await service.set_image(giveaway, message.photo[-1].file_id)
    await message.answer(f"Фото для «{giveaway.title}» обновлено ✅", reply_markup=giveaway_detail_keyboard(giveaway))


# --- edit post url (existing giveaway) ---


@router.callback_query(GiveawayAdminCB.filter(F.action == "set_post_url"))
async def on_giveaway_set_post_url_start(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext, callback_data: GiveawayAdminCB
) -> None:
    service = GiveawayService(session)
    giveaway = await service.get_by_id(callback_data.giveaway_id)
    if giveaway is None:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    await state.update_data(giveaway_id=giveaway.id)
    await state.set_state(GiveawayAdminForm.waiting_for_post_url_edit)
    await callback.message.answer(
        f"Пришлите ссылку на пост в канале для розыгрыша «{giveaway.title}» "
        f"(эта ссылка откроется по кнопке «Открыть пост»):"
    )
    await callback.answer()


@router.message(GiveawayAdminForm.waiting_for_post_url_edit, F.text)
async def on_giveaway_set_post_url(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    await state.set_state(None)

    service = GiveawayService(session)
    giveaway = await service.get_by_id(giveaway_id) if giveaway_id else None
    if giveaway is None:
        await message.answer("Розыгрыш не найден.")
        return

    await service.set_post_url(giveaway, message.text.strip())
    await message.answer(
        f"Ссылка на пост для «{giveaway.title}» обновлена ✅", reply_markup=giveaway_detail_keyboard(giveaway)
    )


# --- edit title/description (existing giveaway) ---


@router.callback_query(GiveawayAdminCB.filter(F.action == "edit_title"))
async def on_giveaway_edit_title_start(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext, callback_data: GiveawayAdminCB
) -> None:
    service = GiveawayService(session)
    giveaway = await service.get_by_id(callback_data.giveaway_id)
    if giveaway is None:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    await state.update_data(giveaway_id=giveaway.id)
    await state.set_state(GiveawayAdminForm.waiting_for_title_edit)
    await callback.message.answer(f"Текущее название: «{giveaway.title}»\nПришлите новое название розыгрыша:")
    await callback.answer()


@router.message(GiveawayAdminForm.waiting_for_title_edit, F.text)
async def on_giveaway_edit_title(message: Message, state: FSMContext) -> None:
    await state.update_data(new_title=message.text)
    await state.set_state(GiveawayAdminForm.waiting_for_description_edit)
    await message.answer("Теперь пришлите новое описание (условия, призы):")


@router.message(GiveawayAdminForm.waiting_for_description_edit, F.text)
async def on_giveaway_edit_description(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    new_title = data.get("new_title")
    await state.set_state(None)

    service = GiveawayService(session)
    giveaway = await service.get_by_id(giveaway_id) if giveaway_id else None
    if giveaway is None:
        await message.answer("Розыгрыш не найден.")
        return

    await service.set_title(giveaway, new_title)
    await service.set_description(giveaway, message.text)
    await message.answer(
        f"Розыгрыш «{giveaway.title}» обновлён ✅", reply_markup=giveaway_detail_keyboard(giveaway)
    )


# --- create ---


@router.callback_query(GiveawayAdminCB.filter(F.action == "create"))
async def on_giveaway_create_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GiveawayAdminForm.waiting_for_title)
    await callback.message.answer("Введите название розыгрыша:")
    await callback.answer()


@router.message(GiveawayAdminForm.waiting_for_title, F.text)
async def on_giveaway_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await state.set_state(GiveawayAdminForm.waiting_for_description)
    await message.answer("Введите описание розыгрыша (условия, призы):")


@router.message(GiveawayAdminForm.waiting_for_description, F.text)
async def on_giveaway_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(GiveawayAdminForm.waiting_for_image)
    await message.answer("Отправьте фото для розыгрыша или нажмите «Без фото»:", reply_markup=_skip_image_keyboard())


async def _to_post_url_step(message_target: Message, state: FSMContext, image_file_id: str | None) -> None:
    await state.update_data(image_file_id=image_file_id)
    await state.set_state(GiveawayAdminForm.waiting_for_post_url)
    await message_target.answer(
        "Пришлите ссылку на пост в канале (для кнопки «Открыть пост») или нажмите «Пропустить»:",
        reply_markup=giveaway_post_url_skip_keyboard(),
    )


@router.message(GiveawayAdminForm.waiting_for_image, F.photo)
async def on_giveaway_image(message: Message, state: FSMContext) -> None:
    await _to_post_url_step(message, state, message.photo[-1].file_id)


@router.callback_query(GiveawayAdminCB.filter(F.action == "img_skip"))
async def on_giveaway_image_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await _to_post_url_step(callback.message, state, None)
    await callback.answer()


async def _finalize_giveaway(
    message_target: Message, session: AsyncSession, state: FSMContext, post_url: str | None
) -> None:
    data = await state.get_data()
    service = GiveawayService(session)
    giveaway = await service.create(
        title=data["title"],
        description=data.get("description"),
        image_file_id=data.get("image_file_id"),
        post_url=post_url,
    )
    await state.set_state(None)
    participants = await service.count_participants(giveaway.id)
    await message_target.answer(f"Розыгрыш «{giveaway.title}» создан ✅ Он сразу доступен пользователям в разделе «Розыгрыш».")
    await message_target.answer(_detail_text(giveaway, participants), reply_markup=giveaway_detail_keyboard(giveaway))


@router.message(GiveawayAdminForm.waiting_for_post_url, F.text)
async def on_giveaway_post_url(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await _finalize_giveaway(message, session, state, message.text.strip())


@router.callback_query(GiveawayAdminCB.filter(F.action == "post_url_skip"))
async def on_giveaway_post_url_skip(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await _finalize_giveaway(callback.message, session, state, None)
    await callback.answer()
