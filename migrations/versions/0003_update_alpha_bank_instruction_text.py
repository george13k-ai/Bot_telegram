"""update alpha_bank_instruction content text

Revision ID: 0003_update_alpha_bank_text
Revises: 0002_giveaway_post_url
Create Date: 2026-09-05
"""

from __future__ import annotations

from sqlalchemy import column, table
from sqlalchemy import String as SAString
from sqlalchemy.sql import update

from alembic import op

revision = "0003_update_alpha_bank_text"
down_revision = "0002_giveaway_post_url"
branch_labels = None
depends_on = None

_content_table = table("content", column("key", SAString), column("text", SAString))

_NEW_TEXT = (
    "Как получить выписку в банке\n\n"
    "🎯1.Обратитесь в свой банк (лично, в приложении Банка в чате поддержки) и "
    "запросите выписку по платежам за весь период с момента открытия кредита или "
    "активации кредитной карты.\n"
    "‼️Инструкция подходит для любого банка, в котором у вас оформлен кредит или "
    "кредитная карта.\n\n"
    "🎯2.Пришлите данный файл или файлы если их несколько в данный чат.\n\n\n"
    "⬇️ВИДЕО ИНСТРУКЦИЯ НИЖЕ⬇️"
)

_OLD_TEXT = (
    "Альфа Банк\n\n"
    "Картинка с инструкцией как получить выписку.\n"
    "Просить у Банка банковские платежи по кредиту или кредитной карте за весь "
    "период с момента активации кредитной карты"
)


def upgrade() -> None:
    op.execute(
        update(_content_table).where(_content_table.c.key == "alpha_bank_instruction").values(text=_NEW_TEXT)
    )


def downgrade() -> None:
    op.execute(
        update(_content_table).where(_content_table.c.key == "alpha_bank_instruction").values(text=_OLD_TEXT)
    )
