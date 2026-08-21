from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.content import content_detail_keyboard, content_list_keyboard
from app.admin.states.content_edit import ContentEdit
from app.database.models.file import FilePurpose, FileType
from app.services.content import ContentService
from app.services.files import FileService
from app.utils.callback_data import AdminMenuCB, ContentCB

router = Router(name="admin_content")

# Content keys whose media is a fixed bot-wide asset tracked in the `files`
# registry (ТЗ п.34) rather than the generic content.media_file_id field.
CONTENT_FILE_PURPOSE: dict[str, tuple[FilePurpose, FileType]] = {
    "alpha_bank_instruction": (FilePurpose.ALPHA_BANK_IMAGE, FileType.PHOTO),
    "pdf_instruction": (FilePurpose.INSTRUCTION_PDF, FileType.DOCUMENT),
}


@router.callback_query(AdminMenuCB.filter(F.section == "content"))
async def on_content_section(callback: CallbackQuery, session: AsyncSession) -> None:
    content = ContentService(session)
    items = await content.list_text_content()
    await callback.message.answer(
        "<b>Контент бота</b>\nВыберите блок для просмотра/редактирования:", reply_markup=content_list_keyboard(items)
    )
    await callback.answer()


@router.callback_query(AdminMenuCB.filter(F.section == "settings"))
async def on_settings_section(callback: CallbackQuery, session: AsyncSession) -> None:
    content = ContentService(session)
    items = await content.list_settings()
    await callback.message.answer(
        "<b>Настройки</b>\nВыберите параметр для изменения:", reply_markup=content_list_keyboard(items)
    )
    await callback.answer()


@router.callback_query(ContentCB.filter(F.action == "list"))
async def on_content_list(callback: CallbackQuery, session: AsyncSession) -> None:
    await on_content_section(callback, session)


@router.callback_query(ContentCB.filter(F.action == "view"))
async def on_content_view(callback: CallbackQuery, session: AsyncSession, callback_data: ContentCB) -> None:
    content = ContentService(session)
    text = await content.get_text(callback_data.key)
    header = f"<b>{callback_data.key}</b>\n\n{text or '(пусто)'}"

    file_id: str | None = None
    if callback_data.key in CONTENT_FILE_PURPOSE:
        purpose, _ = CONTENT_FILE_PURPOSE[callback_data.key]
        files = FileService(session)
        record = await files.get_content_file(purpose)
        file_id = record.telegram_file_id if record else None
    else:
        _, file_id = await content.get_media(callback_data.key)

    if file_id and callback_data.key in CONTENT_FILE_PURPOSE and CONTENT_FILE_PURPOSE[callback_data.key][1] == FileType.PHOTO:
        await callback.message.answer_photo(photo=file_id, caption=header, reply_markup=content_detail_keyboard(callback_data.key))
    elif file_id and callback_data.key in CONTENT_FILE_PURPOSE:
        await callback.message.answer_document(document=file_id, caption=header, reply_markup=content_detail_keyboard(callback_data.key))
    else:
        await callback.message.answer(header, reply_markup=content_detail_keyboard(callback_data.key))
    await callback.answer()


@router.callback_query(ContentCB.filter(F.action == "edit_text"))
async def on_content_edit_text(callback: CallbackQuery, state: FSMContext, callback_data: ContentCB) -> None:
    await state.update_data(content_key=callback_data.key)
    await state.set_state(ContentEdit.waiting_for_text)
    await callback.message.answer(f"Отправьте новый текст для «{callback_data.key}»:")
    await callback.answer()


@router.callback_query(ContentCB.filter(F.action == "edit_media"))
async def on_content_edit_media(callback: CallbackQuery, state: FSMContext, callback_data: ContentCB) -> None:
    await state.update_data(content_key=callback_data.key)
    await state.set_state(ContentEdit.waiting_for_media)
    if callback_data.key in CONTENT_FILE_PURPOSE:
        _, file_type = CONTENT_FILE_PURPOSE[callback_data.key]
        prompt = "Отправьте новое фото" if file_type == FileType.PHOTO else "Отправьте новый файл (документ)"
    else:
        prompt = "Отправьте новое фото"
    await callback.message.answer(f"{prompt} для «{callback_data.key}»:")
    await callback.answer()


@router.message(ContentEdit.waiting_for_text, F.text)
async def on_content_new_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("content_key")
    if not key:
        await state.set_state(None)
        return
    content = ContentService(session)
    await content.set_text(key, message.text, updated_by=message.from_user.id)
    await state.set_state(None)
    await message.answer(f"Текст «{key}» обновлён ✅")


@router.message(ContentEdit.waiting_for_media, F.photo)
async def on_content_new_photo(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("content_key")
    if not key:
        await state.set_state(None)
        return

    photo = message.photo[-1]
    if key in CONTENT_FILE_PURPOSE:
        purpose, _ = CONTENT_FILE_PURPOSE[key]
        files = FileService(session)
        await files.set_content_file(
            purpose, photo.file_id, FileType.PHOTO, uploaded_by=message.from_user.id, size=photo.file_size
        )
    else:
        content = ContentService(session)
        await content.set_media(key, media_type="photo", media_file_id=photo.file_id, updated_by=message.from_user.id)

    await state.set_state(None)
    await message.answer(f"Медиа для «{key}» обновлено ✅")


@router.message(ContentEdit.waiting_for_media, F.document)
async def on_content_new_document(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("content_key")
    if not key or key not in CONTENT_FILE_PURPOSE:
        await state.set_state(None)
        return

    purpose, _ = CONTENT_FILE_PURPOSE[key]
    document = message.document
    files = FileService(session)
    await files.set_content_file(
        purpose,
        document.file_id,
        FileType.DOCUMENT,
        uploaded_by=message.from_user.id,
        file_name=document.file_name,
        mime_type=document.mime_type,
        size=document.file_size,
    )
    await state.set_state(None)
    await message.answer(f"Файл для «{key}» обновлён ✅")
