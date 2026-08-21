from __future__ import annotations

from datetime import datetime

from app.database.models.user import User

DATE_FORMAT = "%d.%m.%Y в %H:%M"


def format_user_mention(user: User) -> str:
    label = f"@{user.username}" if user.username else (user.first_name or str(user.telegram_id))
    return f'<a href="{user.mention_link}">{label}</a>'


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime(DATE_FORMAT)


def format_amount(amount: float | None) -> str:
    if amount is None:
        return "не определена"
    return f"{amount:,.0f} рублей".replace(",", " ")
