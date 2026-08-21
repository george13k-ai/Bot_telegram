from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.menu import back_to_admin_menu_keyboard
from app.services.statistics import StatisticsService
from app.utils.callback_data import AdminMenuCB

router = Router(name="admin_statistics")


@router.callback_query(AdminMenuCB.filter(F.section == "statistics"))
async def on_statistics_section(callback: CallbackQuery, session: AsyncSession) -> None:
    service = StatisticsService(session)
    stats = await service.collect()
    await callback.message.answer(service.format_report(stats), reply_markup=back_to_admin_menu_keyboard())
    await callback.answer()
