from __future__ import annotations

import pytest

from app.services.files import FileService, FileValidationError, ALLOWED_USER_DOCUMENT_MIME_TYPES
from app.services.users import UsersService


async def _make_user(session, telegram_id: int):
    users = UsersService(session)
    user, _ = await users.get_or_create(telegram_id=telegram_id, username=None, first_name="U", last_name=None)
    await session.commit()
    return user


def test_pdf_mime_type_is_allowed():
    service = FileService(session=None)  # validate_user_document doesn't touch the DB
    service.validate_user_document("application/pdf", 1024)


def test_non_pdf_mime_type_is_rejected():
    service = FileService(session=None)
    with pytest.raises(FileValidationError):
        service.validate_user_document("image/jpeg", 1024)


def test_oversized_pdf_is_rejected():
    from app.config import settings

    service = FileService(session=None)
    with pytest.raises(FileValidationError):
        service.validate_user_document("application/pdf", settings.max_file_size_bytes + 1)


async def test_save_user_document_persists_record(session):
    user = await _make_user(session, 3001)
    files = FileService(session)

    user_file = await files.save_user_document(
        user_id=user.id,
        telegram_file_id="FILE_ID_123",
        file_name="statement.pdf",
        mime_type="application/pdf",
        file_size=2048,
    )
    await session.commit()

    stored = await files.repo.list_for_user(user.id)
    assert len(stored) == 1
    assert stored[0].telegram_file_id == "FILE_ID_123"
    assert stored[0].id == user_file.id


def test_allowed_mime_types_is_pdf_only():
    assert ALLOWED_USER_DOCUMENT_MIME_TYPES == {"application/pdf"}
