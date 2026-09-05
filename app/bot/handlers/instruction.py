from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import specialist_only_keyboard
from app.bot.keyboards.instruction import pdf_instruction_keyboard
from app.database.models.file import FilePurpose
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.services.content import ContentService
from app.services.files import FileService
from app.utils.callback_data import InstructionCB

router = Router(name="instruction")


@router.callback_query(InstructionCB.filter(F.action == "get"))
async def on_instruction_get(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    events = EventRepository(session)
    await events.log(db_user.id, EventType.INSTRUCTION_REQUESTED)

    content = ContentService(session)
    files = FileService(session)

    intro_text = await content.get_text("instruction_message")
    await callback.message.answer(intro_text)

    alpha_bank_text = await content.get_text("alpha_bank_instruction")
    alpha_bank_image = await files.get_content_file(FilePurpose.ALPHA_BANK_IMAGE)
    if alpha_bank_image is not None:
        await callback.message.answer_photo(photo=alpha_bank_image.telegram_file_id, caption=alpha_bank_text)
    else:
        await callback.message.answer(alpha_bank_text)

    pdf_text = await content.get_text("pdf_instruction")
    instruction_pdf = await files.get_content_file(FilePurpose.INSTRUCTION_PDF)
    if instruction_pdf is not None:
        await callback.message.answer_document(
            document=instruction_pdf.telegram_file_id, caption=pdf_text, reply_markup=pdf_instruction_keyboard()
        )
    else:
        await callback.message.answer(pdf_text, reply_markup=pdf_instruction_keyboard())
    await events.log(db_user.id, EventType.PDF_SENT)

    await callback.answer()


@router.callback_query(InstructionCB.filter(F.action == "video"))
async def on_instruction_video(callback: CallbackQuery, session: AsyncSession) -> None:
    content = ContentService(session)
    media_type, media_file_id = await content.get_media("pdf_video_instruction")
    caption = await content.get_text("pdf_video_instruction")

    if media_file_id and media_type == "video_note":
        await callback.message.answer_video_note(video_note=media_file_id)
        await callback.message.answer(caption, reply_markup=specialist_only_keyboard())
    elif media_file_id and media_type == "video":
        try:
            await callback.message.answer_video(
                video=media_file_id, caption=caption, reply_markup=specialist_only_keyboard()
            )
        except TelegramBadRequest:
            # Формат/кодек не проигрывается как видео в Telegram - отдаём файлом,
            # чтобы пользователь всё равно мог его скачать и посмотреть.
            await callback.message.answer_document(
                document=media_file_id, caption=caption, reply_markup=specialist_only_keyboard()
            )
    else:
        await callback.message.answer(
            "Видео-инструкция пока не загружена. Напишите специалисту — он поможет разобраться.",
            reply_markup=specialist_only_keyboard(),
        )
    await callback.answer()
