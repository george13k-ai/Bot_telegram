from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.giveaways import giveaway_detail_keyboard, giveaways_list_keyboard
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
    text = (
        f"<b>{giveaway.title}</b>\n\n"
        f"{giveaway.description or ''}\n\n"
        f"Активен: {'да' if giveaway.is_active else 'нет'}\n"
        f"Создан: {format_datetime(giveaway.created_at)}\n"
        f"Участников: {participants}"
    )
    await callback.message.answer(text, reply_markup=giveaway_detail_keyboard(giveaway))
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


async def _finalize_giveaway(message_target: Message, session: AsyncSession, state: FSMContext, image_file_id: str | None) -> None:
    data = await state.get_data()
    service = GiveawayService(session)
    giveaway = await service.create(title=data["title"], description=data.get("description"), image_file_id=image_file_id)
    await state.set_state(None)
    await message_target.answer(f"Розыгрыш «{giveaway.title}» создан ✅")


@router.message(GiveawayAdminForm.waiting_for_image, F.photo)
async def on_giveaway_image(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await _finalize_giveaway(message, session, state, message.photo[-1].file_id)


@router.callback_query(GiveawayAdminCB.filter(F.action == "img_skip"))
async def on_giveaway_image_skip(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    await _finalize_giveaway(callback.message, session, state, None)
    await callback.answer()
