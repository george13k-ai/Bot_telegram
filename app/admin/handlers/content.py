from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.keyboards.content import content_detail_keyboard, content_list_keyboard
from app.admin.states.content_edit import ContentEdit
from app.database.models.file import FilePurpose, FileType
from app.services.content import ContentService, content_label
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
    header = f"<b>{content_label(callback_data.key)}</b>\n\n{text or '(пусто)'}"

    file_id: str | None = None
    media_type: str | None = None
    if callback_data.key in CONTENT_FILE_PURPOSE:
        purpose, _ = CONTENT_FILE_PURPOSE[callback_data.key]
        files = FileService(session)
        record = await files.get_content_file(purpose)
        file_id = record.telegram_file_id if record else None
    else:
        media_type, file_id = await content.get_media(callback_data.key)

    keyboard = content_detail_keyboard(callback_data.key)
    if file_id and callback_data.key in CONTENT_FILE_PURPOSE and CONTENT_FILE_PURPOSE[callback_data.key][1] == FileType.PHOTO:
        await callback.message.answer_photo(photo=file_id, caption=header, reply_markup=keyboard)
    elif file_id and callback_data.key in CONTENT_FILE_PURPOSE:
        await callback.message.answer_document(document=file_id, caption=header, reply_markup=keyboard)
    elif file_id and media_type == "video_note":
        await callback.message.answer_video_note(video_note=file_id)
        await callback.message.answer(header, reply_markup=keyboard)
    elif file_id and media_type == "video":
        try:
            await callback.message.answer_video(video=file_id, caption=header, reply_markup=keyboard)
        except TelegramBadRequest:
            # Некоторые форматы/кодеки Telegram не может проиграть как видео -
            # но файл сохранён, отдаём его как обычный документ.
            await callback.message.answer_document(document=file_id, caption=header, reply_markup=keyboard)
    elif file_id:
        await callback.message.answer_photo(photo=file_id, caption=header, reply_markup=keyboard)
    else:
        await callback.message.answer(header, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(ContentCB.filter(F.action == "edit_text"))
async def on_content_edit_text(callback: CallbackQuery, state: FSMContext, callback_data: ContentCB) -> None:
    await state.update_data(content_key=callback_data.key)
    await state.set_state(ContentEdit.waiting_for_text)
    await callback.message.answer(f"Отправьте новый текст для «{content_label(callback_data.key)}»:")
    await callback.answer()


@router.callback_query(ContentCB.filter(F.action == "toggle_bool"))
async def on_content_toggle_bool(callback: CallbackQuery, session: AsyncSession, callback_data: ContentCB) -> None:
    content = ContentService(session)
    if callback_data.key == "setting_require_join_approval":
        new_value = not await content.get_require_join_approval()
        await content.set_require_join_approval(new_value, updated_by=callback.from_user.id)
        state_text = "включено ✅" if new_value else "выключено ❌"
        await callback.message.answer(
            f"«{content_label(callback_data.key)}»: {state_text}\n\n"
            + (
                "Теперь заявка на вступление в канал засчитывается как подписка "
                "(одобрять можно позже вручную)."
                if new_value
                else "Теперь для участия нужно фактическое членство в канале."
            ),
            reply_markup=content_detail_keyboard(callback_data.key),
        )
    await callback.answer()


@router.callback_query(ContentCB.filter(F.action == "edit_media"))
async def on_content_edit_media(callback: CallbackQuery, state: FSMContext, callback_data: ContentCB) -> None:
    await state.update_data(content_key=callback_data.key)
    await state.set_state(ContentEdit.waiting_for_media)
    if callback_data.key in CONTENT_FILE_PURPOSE:
        _, file_type = CONTENT_FILE_PURPOSE[callback_data.key]
        prompt = "Отправьте новое фото" if file_type == FileType.PHOTO else "Отправьте новый файл (документ)"
    else:
        prompt = "Отправьте новое фото или видео (любым способом - как видео, кружком или файлом)"
    await callback.message.answer(f"{prompt} для «{content_label(callback_data.key)}»:")
    await callback.answer()


@router.message(ContentEdit.waiting_for_text, F.text)
async def on_content_new_text(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("content_key")
    if not key:
        await state.set_state(None)
        return
    content = ContentService(session)
    await state.set_state(None)

    if key == "setting_channel_url":
        username = await content.set_channel_url(message.text.strip(), updated_by=message.from_user.id)
        if username:
            await message.answer(
                f"Ссылка на канал обновлена ✅\nПроверка подписки теперь тоже идёт по каналу @{username}."
            )
        else:
            await message.answer(
                "Ссылка на канал обновлена ✅\n\n"
                "Похоже, это приватная ссылка - чтобы проверка подписки тоже заработала на новом канале, "
                "укажите его числовой ID в «🆔 ID канала для проверки подписки» (Настройки)."
            )
        return

    await content.set_text(key, message.text, updated_by=message.from_user.id)
    await message.answer(f"Текст «{content_label(key)}» обновлён ✅")


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
    await message.answer(f"Медиа для «{content_label(key)}» обновлено ✅")


@router.message(ContentEdit.waiting_for_media, F.video)
async def on_content_new_video(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("content_key")
    if not key or key in CONTENT_FILE_PURPOSE:
        await state.set_state(None)
        return

    content = ContentService(session)
    await content.set_media(key, media_type="video", media_file_id=message.video.file_id, updated_by=message.from_user.id)
    await state.set_state(None)
    await message.answer(f"Видео для «{content_label(key)}» обновлено ✅")


@router.message(ContentEdit.waiting_for_media, F.video_note)
async def on_content_new_video_note(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("content_key")
    if not key or key in CONTENT_FILE_PURPOSE:
        await state.set_state(None)
        return

    content = ContentService(session)
    await content.set_media(
        key, media_type="video_note", media_file_id=message.video_note.file_id, updated_by=message.from_user.id
    )
    await state.set_state(None)
    await message.answer(f"Видео (кружок) для «{content_label(key)}» обновлено ✅")


@router.message(ContentEdit.waiting_for_media, F.document)
async def on_content_new_document(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    key = data.get("content_key")
    if not key:
        await state.set_state(None)
        return

    document = message.document

    if key in CONTENT_FILE_PURPOSE:
        purpose, _ = CONTENT_FILE_PURPOSE[key]
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
        await message.answer(f"Файл для «{content_label(key)}» обновлён ✅")
        return

    # Некоторые видео (необычные кодеки/контейнеры, отправка "файлом") Telegram
    # доставляет как документ, а не как message.video - принимаем и такие,
    # чтобы видео-инструкцию можно было загрузить в любом формате.
    if document.mime_type and document.mime_type.startswith("video/"):
        content = ContentService(session)
        await content.set_media(
            key, media_type="video", media_file_id=document.file_id, updated_by=message.from_user.id
        )
        await state.set_state(None)
        await message.answer(f"Видео для «{content_label(key)}» обновлено ✅")
        return

    await state.set_state(None)
    await message.answer("Для этого раздела нужно фото или видео. Пришлите файл ещё раз в подходящем формате.")
