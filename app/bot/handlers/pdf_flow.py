from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import specialist_only_keyboard
from app.database.models.notification import NotificationType
from app.database.models.user import User
from app.database.models.user_event import EventType
from app.database.repositories.event_repo import EventRepository
from app.services.calculation import CalculationService
from app.services.content import ContentService
from app.services.files import FileService, FileValidationError
from app.services.notifications import NotificationService
from app.services.specialist import SpecialistService
from app.services.tags import TagService
from app.utils.formatting import format_amount, format_datetime
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = Router(name="pdf_flow")


async def _download_and_calculate(bot, document, keyword: str) -> float | None:
    try:
        file_obj = await bot.download(document.file_id)
    except Exception as exc:  # noqa: BLE001 - сетевые/API-ошибки не должны рвать сценарий
        logger.warning("pdf_download_failed", file_id=document.file_id, error=str(exc))
        return None

    pdf_bytes = file_obj.read()
    calculation = CalculationService()
    return calculation.calculate_from_pdf_bytes(pdf_bytes, keyword)


@router.message(F.document)
async def on_document_received(message: Message, session: AsyncSession, db_user: User, bot) -> None:
    document = message.document
    files = FileService(session)
    content = ContentService(session)

    try:
        files.validate_user_document(document.mime_type, document.file_size)
    except FileValidationError as exc:
        await message.answer(str(exc), reply_markup=specialist_only_keyboard())
        return

    specialist_service = SpecialistService(session)
    ticket = await specialist_service.register_pdf_upload(db_user.id)

    await files.save_user_document(
        user_id=db_user.id,
        telegram_file_id=document.file_id,
        file_name=document.file_name,
        mime_type=document.mime_type,
        file_size=document.file_size,
        ticket_id=ticket.id,
    )

    tags = TagService(session)
    await tags.mark_pro(db_user.id)

    keyword = await content.get_calculation_keyword()
    amount = await _download_and_calculate(bot, document, keyword)
    await specialist_service.set_calculated_amount(ticket, amount)
    await specialist_service.mark_waiting_for_admin(ticket)

    events = EventRepository(session)
    await events.log(db_user.id, EventType.FILE_UPLOADED, {"file_name": document.file_name, "amount": amount})

    notifications = NotificationService(bot, session)
    extra_note = (
        f"Пользователь отправил файл: {document.file_name or 'документ'}\n"
        f"Заявка №{ticket.id}, файл получен {format_datetime(ticket.updated_at)}"
    )
    summary = await notifications.build_user_summary(db_user, ticket, extra_note=extra_note)
    await notifications.notify_admins(
        NotificationType.NEW_PDF, db_user, summary, ticket_id=ticket.id, document_file_id=document.file_id
    )

    status_line = (
        f"Файл получен ✅ (заявка №{ticket.id})\nСтатус: {ticket.status_label}\n"
        f"Страховка на сумму: {format_amount(amount)}"
    )
    await message.answer(status_line)

    if amount is None:
        pending_text = await content.get_text("ticket_pending_amount_message")
        await message.answer(pending_text, reply_markup=specialist_only_keyboard())


@router.message(F.content_type.in_({"photo", "video", "audio", "voice", "sticker"}))
async def on_wrong_media_type(message: Message) -> None:
    await message.answer(
        "Пожалуйста, отправьте файл в формате PDF документом (не фото/видео). "
        "Если не получается — напишите специалисту.",
        reply_markup=specialist_only_keyboard(),
    )
