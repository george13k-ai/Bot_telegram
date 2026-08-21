from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.subscriptions import subscriptions_keyboard
from app.services.content import ContentService
from app.services.users import UsersService
from app.utils.callback_data import AdminMenuCB

router = Router(name="admin_subscriptions")


@router.callback_query(AdminMenuCB.filter(F.section == "subscriptions"))
async def on_subscriptions_section(callback: CallbackQuery, session: AsyncSession) -> None:
    users_service = UsersService(session)
    content = ContentService(session)

    total = await users_service.count_all()
    subscribed = await users_service.repo.count_subscribed()
    channel_url = await content.get_channel_url()
    channel_name = await content.get_channel_name()

    percent = round(subscribed / total * 100, 1) if total else 0

    text = (
        "<b>Подписки</b>\n\n"
        f"Канал: {channel_name}\n"
        f"Ссылка: {channel_url}\n\n"
        f"Подписано: {subscribed} из {total} ({percent}%)"
    )
    await callback.message.answer(text, reply_markup=subscriptions_keyboard())
    await callback.answer()
