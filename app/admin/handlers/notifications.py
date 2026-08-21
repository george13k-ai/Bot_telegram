from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.menu import back_to_admin_menu_keyboard
from app.admin.states.admin_reply import AdminReply
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.database.repositories.notification_repo import NotificationRepository
from app.services.specialist import SpecialistService
from app.utils.callback_data import AdminMenuCB, NotificationCB
from app.utils.formatting import format_datetime

router = Router(name="admin_notifications")


@router.callback_query(AdminMenuCB.filter(F.section == "notifications"))
async def on_notifications_section(callback: CallbackQuery, session: AsyncSession) -> None:
    repo = NotificationRepository(session)
    notifications = await repo.list_recent(limit=15)
    if not notifications:
        await callback.message.answer("Уведомлений пока нет.", reply_markup=back_to_admin_menu_keyboard())
        await callback.answer()
        return

    lines = ["<b>Последние уведомления</b>", ""]
    for n in notifications:
        mark = "✅" if n.is_answered else "🕓"
        lines.append(f"{mark} #{n.id} [{n.type.value}] {format_datetime(n.created_at)}")
    await callback.message.answer("\n".join(lines), reply_markup=back_to_admin_menu_keyboard())
    await callback.answer()


@router.callback_query(NotificationCB.filter(F.action == "reply"))
async def on_notification_reply(callback: CallbackQuery, state: FSMContext, callback_data: NotificationCB) -> None:
    await state.update_data(
        notification_id=callback_data.notification_id,
        ticket_id=callback_data.ticket_id,
        user_id=callback_data.user_id,
    )
    await state.set_state(AdminReply.waiting_for_reply)
    await callback.message.answer("Напишите ответ пользователю:")
    await callback.answer()


@router.message(AdminReply.waiting_for_reply, F.text)
async def on_admin_reply_text(message: Message, session: AsyncSession, state: FSMContext, bot) -> None:
    data = await state.get_data()
    user_id = data.get("user_id")
    ticket_id = data.get("ticket_id")
    notification_id = data.get("notification_id")

    if user_id is None:
        await message.answer("Не удалось определить пользователя для ответа.")
        await state.set_state(None)
        return

    user = await session.get(User, user_id)
    if user is None:
        await message.answer("Пользователь не найден.")
        await state.set_state(None)
        return

    try:
        await bot.send_message(chat_id=user.telegram_id, text=message.text)
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        await message.answer(f"Не удалось отправить сообщение пользователю: {exc}")
        await state.set_state(None)
        return

    if ticket_id is not None:
        specialist_service = SpecialistService(session)
        ticket = await specialist_service.get_ticket(ticket_id)
        if ticket is not None:
            await specialist_service.add_admin_reply(ticket, message.text)

    if notification_id is not None:
        from app.services.notifications import NotificationService

        notifications = NotificationService(bot, session)
        await notifications.mark_answered(notification_id, message.from_user.id)

    events = EventRepository(session)
    await events.log(user.id, EventType.ADMIN_REPLY, {"admin_id": message.from_user.id})

    await message.answer("Вы ответили ✅")
    await state.set_state(None)
