from __future__ import annotations

from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.mailings import (
    audience_keyboard,
    audience_tag_keyboard,
    confirm_keyboard,
    mailing_detail_keyboard,
    mailings_list_keyboard,
    mailings_menu_keyboard,
    photo_choice_keyboard,
    preview_keyboard,
    time_keyboard,
)
from app.admin.states.mailing import MailingCreate
from app.database.models.mailing import AudienceType
from app.services import scheduler as scheduler_service
from app.services.mailings import MailingService
from app.services.tags import TagService
from app.utils.callback_data import AdminMenuCB, MailingCB
from app.utils.formatting import format_datetime

router = Router(name="admin_mailings")

PAGE_SIZE = 10

AUDIENCE_LABELS = {
    AudienceType.ALL: "Все пользователи",
    AudienceType.ACTIVATED: "Активированные",
    AudienceType.TAG: "По тегу",
    AudienceType.FILE_SENT: "Отправившие файл",
}


@router.callback_query(AdminMenuCB.filter(F.section == "mailings"))
async def on_mailings_section(callback: CallbackQuery) -> None:
    await callback.message.answer("<b>Рассылки</b>", reply_markup=mailings_menu_keyboard())
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "menu"))
async def on_mailings_menu(callback: CallbackQuery) -> None:
    await callback.message.answer("<b>Рассылки</b>", reply_markup=mailings_menu_keyboard())
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "list"))
async def on_mailings_list(callback: CallbackQuery, session: AsyncSession, callback_data: MailingCB) -> None:
    service = MailingService(callback.bot, session)
    mailings = await service.list_all(limit=PAGE_SIZE + 1, offset=callback_data.page * PAGE_SIZE)
    has_next = len(mailings) > PAGE_SIZE
    mailings = mailings[:PAGE_SIZE]
    await callback.message.answer(
        "<b>Все рассылки</b>", reply_markup=mailings_list_keyboard(mailings, callback_data.page, has_next)
    )
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "view"))
async def on_mailing_view(callback: CallbackQuery, session: AsyncSession, callback_data: MailingCB) -> None:
    service = MailingService(callback.bot, session)
    mailing = await service.get(callback_data.mailing_id)
    if mailing is None:
        await callback.answer("Рассылка не найдена", show_alert=True)
        return
    text = (
        f"<b>Рассылка #{mailing.id}</b>\n"
        f"Статус: {mailing.status.value}\n"
        f"Аудитория: {AUDIENCE_LABELS.get(mailing.audience_type, mailing.audience_type.value)}\n"
        f"Запланирована: {format_datetime(mailing.scheduled_at)}\n\n"
        f"Текст:\n{mailing.text}\n\n"
        f"Всего: {mailing.total} | Отправлено: {mailing.sent} | Ошибок: {mailing.failed} | Заблокировали: {mailing.blocked}"
    )
    await callback.message.answer(text, reply_markup=mailing_detail_keyboard(mailing))
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "cancel"))
async def on_mailing_cancel(
    callback: CallbackQuery, session: AsyncSession, callback_data: MailingCB, scheduler: AsyncIOScheduler
) -> None:
    service = MailingService(callback.bot, session)
    mailing = await service.get(callback_data.mailing_id)
    if mailing is None:
        await callback.answer("Рассылка не найдена", show_alert=True)
        return
    await service.cancel(mailing)
    scheduler_service.cancel_scheduled_mailing(scheduler, mailing.id)
    await callback.message.answer("Рассылка успешно отменена!", reply_markup=mailings_menu_keyboard())
    await callback.answer()


# --- creation flow ---


@router.callback_query(MailingCB.filter(F.action == "create"))
async def on_mailing_create_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MailingCreate.waiting_for_text)
    await callback.message.answer("Напишите текст рассылки:")
    await callback.answer()


@router.message(MailingCreate.waiting_for_text, F.text)
async def on_mailing_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=message.text)
    await message.answer("Добавить фото к рассылке?", reply_markup=photo_choice_keyboard())


@router.callback_query(MailingCB.filter(F.action == "add_photo"))
async def on_mailing_add_photo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MailingCreate.waiting_for_photo)
    await callback.message.answer("Отправьте фото для рассылки:")
    await callback.answer()


async def _show_preview(target: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = data.get("text", "")
    photo_file_id = data.get("photo_file_id")
    if photo_file_id:
        await target.answer_photo(photo=photo_file_id, caption=text, reply_markup=preview_keyboard())
    else:
        await target.answer(text, reply_markup=preview_keyboard())


@router.message(MailingCreate.waiting_for_photo, F.photo)
async def on_mailing_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await state.set_state(None)
    await _show_preview(message, state)


@router.callback_query(MailingCB.filter(F.action == "no_photo"))
async def on_mailing_no_photo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(photo_file_id=None)
    await state.set_state(None)
    await _show_preview(callback.message, state)
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "preview_no"))
async def on_mailing_preview_no(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MailingCreate.waiting_for_text)
    await callback.message.answer("Напишите новый текст рассылки:")
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "preview_ok"))
async def on_mailing_preview_ok(callback: CallbackQuery) -> None:
    await callback.message.answer("Выберите аудиторию рассылки:", reply_markup=audience_keyboard())
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "audience_all"))
async def on_audience_all(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(audience_type=AudienceType.ALL.value, audience_filter=None)
    await callback.message.answer("Когда отправить рассылку?", reply_markup=time_keyboard())
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "audience_activated"))
async def on_audience_activated(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(audience_type=AudienceType.ACTIVATED.value, audience_filter=None)
    await callback.message.answer("Когда отправить рассылку?", reply_markup=time_keyboard())
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "audience_file_sent"))
async def on_audience_file_sent(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(audience_type=AudienceType.FILE_SENT.value, audience_filter=None)
    await callback.message.answer("Когда отправить рассылку?", reply_markup=time_keyboard())
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "audience_tag"))
async def on_audience_tag(callback: CallbackQuery, session: AsyncSession) -> None:
    tags_service = TagService(session)
    tags = await tags_service.list_all()
    if not tags:
        await callback.answer("Тегов пока нет", show_alert=True)
        return
    await callback.message.answer("Выберите тег:", reply_markup=audience_tag_keyboard(tags))
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "audience_tag_pick"))
async def on_audience_tag_pick(callback: CallbackQuery, state: FSMContext, callback_data: MailingCB) -> None:
    await state.update_data(
        audience_type=AudienceType.TAG.value, audience_filter={"tag_id": callback_data.tag_id}
    )
    await callback.message.answer("Когда отправить рассылку?", reply_markup=time_keyboard())
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "time_now"))
async def on_time_now(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(scheduled_at=None)
    await _show_confirm(callback.message, state)
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "time_2h"))
async def on_time_2h(callback: CallbackQuery, state: FSMContext) -> None:
    run_at = datetime.now() + timedelta(hours=2)
    await state.update_data(scheduled_at=run_at.isoformat())
    await _show_confirm(callback.message, state)
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "time_custom"))
async def on_time_custom(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MailingCreate.waiting_for_custom_time)
    await callback.message.answer("Введите дату и время отправки в формате ДД.ММ.ГГГГ ЧЧ:ММ (например 25.12.2026 18:00):")
    await callback.answer()


@router.message(MailingCreate.waiting_for_custom_time, F.text)
async def on_time_custom_input(message: Message, state: FSMContext) -> None:
    try:
        run_at = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("Неверный формат. Введите дату как ДД.ММ.ГГГГ ЧЧ:ММ:")
        return
    if run_at <= datetime.now():
        await message.answer("Дата должна быть в будущем. Введите ещё раз:")
        return
    await state.update_data(scheduled_at=run_at.isoformat())
    await state.set_state(None)
    await _show_confirm(message, state)


async def _show_confirm(target: Message, state: FSMContext) -> None:
    data = await state.get_data()
    audience_label = AUDIENCE_LABELS.get(AudienceType(data["audience_type"]), data["audience_type"])
    scheduled_at = data.get("scheduled_at")
    when_label = "сейчас" if not scheduled_at else format_datetime(datetime.fromisoformat(scheduled_at))
    summary = (
        "<b>Подтверждение рассылки</b>\n\n"
        f"Аудитория: {audience_label}\n"
        f"Время отправки: {when_label}\n\n"
        f"Текст:\n{data.get('text', '')}"
    )
    await target.answer(summary, reply_markup=confirm_keyboard())


@router.callback_query(MailingCB.filter(F.action == "cancel_draft"))
async def on_mailing_cancel_draft(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)
    await state.update_data(text=None, photo_file_id=None, audience_type=None, audience_filter=None, scheduled_at=None)
    await callback.message.answer("Рассылка успешно отменена!", reply_markup=mailings_menu_keyboard())
    await callback.answer()


@router.callback_query(MailingCB.filter(F.action == "confirm"))
async def on_mailing_confirm(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext, scheduler: AsyncIOScheduler
) -> None:
    data = await state.get_data()
    service = MailingService(callback.bot, session)

    mailing = await service.create_draft(
        text=data.get("text", ""), photo_file_id=data.get("photo_file_id"), created_by=callback.from_user.id
    )

    audience_type = AudienceType(data["audience_type"])
    audience_filter = data.get("audience_filter")
    scheduled_at_raw = data.get("scheduled_at")
    scheduled_at = datetime.fromisoformat(scheduled_at_raw) if scheduled_at_raw else None

    recipients_count = await service.finalize_setup(mailing, audience_type, audience_filter, scheduled_at)
    await session.commit()

    if scheduled_at is None:
        scheduler_service.schedule_mailing_now(scheduler, mailing.id)
        await callback.message.answer(
            f"Рассылка запущена! Получателей: {recipients_count}", reply_markup=mailings_menu_keyboard()
        )
    else:
        scheduler_service.schedule_mailing(scheduler, mailing.id, scheduled_at)
        await callback.message.answer(
            f"Рассылка запланирована на {format_datetime(scheduled_at)}. Получателей: {recipients_count}",
            reply_markup=mailings_menu_keyboard(),
        )

    await state.set_state(None)
    await state.update_data(text=None, photo_file_id=None, audience_type=None, audience_filter=None, scheduled_at=None)
    await callback.answer()
