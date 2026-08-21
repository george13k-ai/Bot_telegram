from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.menu import admin_main_menu_keyboard
from app.admin.states.auth import AdminAuth
from app.config import settings
from app.database.models.admin import Admin
from app.utils.callback_data import AdminMenuCB
from datetime import datetime, timezone
from sqlalchemy import select

router = Router(name="admin_menu")


async def _register_admin_login(session: AsyncSession, telegram_id: int) -> None:
    result = await session.execute(select(Admin).where(Admin.telegram_id == telegram_id))
    admin = result.scalar_one_or_none()
    if admin is None:
        admin = Admin(telegram_id=telegram_id)
        session.add(admin)
    admin.last_login_at = datetime.now(timezone.utc)
    await session.flush()


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if settings.ADMIN_SECRET_KEY:
        data = await state.get_data()
        if not data.get("admin_authenticated"):
            await state.set_state(AdminAuth.waiting_for_code)
            await message.answer("Введите код доступа к админ-панели:")
            return

    await _register_admin_login(session, message.from_user.id)
    await state.set_state(None)
    await message.answer("Админ-панель", reply_markup=admin_main_menu_keyboard())


@router.message(AdminAuth.waiting_for_code, F.text)
async def on_admin_code(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text.strip() != settings.ADMIN_SECRET_KEY:
        await message.answer("Неверный код. Попробуйте ещё раз:")
        return

    await _register_admin_login(session, message.from_user.id)
    await state.update_data(admin_authenticated=True)
    await state.set_state(None)
    await message.answer("Доступ подтверждён.\n\nАдмин-панель", reply_markup=admin_main_menu_keyboard())


@router.callback_query(AdminMenuCB.filter(F.section == "home"))
async def on_admin_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(None)
    await callback.message.answer("Админ-панель", reply_markup=admin_main_menu_keyboard())
    await callback.answer()
