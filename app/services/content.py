from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.content_repo import ContentRepository
from app.config import settings

# Default texts, editable at runtime by admins via the Content admin section.
# These come directly from the concept (ТЗ) and are seeded into the `content`
# table on first run so the bot works out of the box.
DEFAULT_CONTENT: dict[str, str] = {
    "start_message": (
        "Привет, меня зовут ИИ Ассистент.\n"
        "Я ИИ Ассистент по возврату переплаты по кредитам и кредитным картам.\n"
        "Хочешь я помогу тебе вернуть переплату?"
    ),
    "subscription_message": (
        "Чтобы я помог тебе вернуть переплату, тебе нужно подписаться на мой "
        "информационный инсайдерский канал «{channel_name}»"
    ),
    "subscribed_message": (
        "Спасибо что подписался, теперь ты будешь в курсе всех последних новостей "
        "о которых тебе не расскажут по ТЕЛЕВИЗОРУ"
    ),
    "why_message": (
        "Чтобы помочь тебе вернуть переплату, тебе нужно ознакомиться со всей "
        "информацией по инструкции."
    ),
    "instruction_message": (
        "Инструкция по возврату переплаты. Внимательно ознакомься с информацией ниже."
    ),
    "alpha_bank_instruction": (
        "Как получить выписку в банке\n\n"
        "🎯1.Обратитесь в свой банк (лично, в приложении Банка в чате поддержки) и "
        "запросите выписку по платежам за весь период с момента открытия кредита или "
        "активации кредитной карты.\n"
        "‼️Инструкция подходит для любого банка, в котором у вас оформлен кредит или "
        "кредитная карта.\n\n"
        "🎯2.Пришлите данный файл или файлы если их несколько в данный чат.\n\n\n"
        "⬇️ВИДЕО ИНСТРУКЦИЯ НИЖЕ⬇️"
    ),
    "pdf_instruction": (
        "Видео инструкции как отправить файл боту!\n"
        "❗ ВАЖНО ❗\n"
        "Пришлите файл PDF в этот чат.\n\n"
        "Если не получится, вы можете написать специалисту."
    ),
    "pdf_video_instruction": "Видео-инструкция: как отправить файл боту.",
    "specialist_message": "Напишите ваше сообщение специалисту, он ответит вам в ближайшее время.",
    "giveaway_message": (
        "Участвуй в бесплатном розыгрыше!\n\n"
        "Каждый месяц 3 машины, 25 новых iPhone 17 pro и 250 человек получат по 20.000 рублей\n\n"
        "Чтобы участвовать: подпишись на канал, открой пост и поставь под ним реакцию — это всё!"
    ),
    "ticket_pending_amount_message": (
        "Если бот не смог самостоятельно понять сколько можно вернуть и отправить ваши "
        "данные, мы можем отправить заявку специалисту."
    ),
    "reminder_user_message": (
        "Не получилось получить файл от банка? Я могу помочь — просто напиши специалисту, "
        "и мы разберёмся вместе."
    ),
    "unsubscribe_reminder_message": (
        "Вы отписались от канала «{channel_name}» — а без подписки участвовать в розыгрыше "
        "и получать инсайды не получится. Подпишитесь снова, чтобы не пропустить!"
    ),
    # Runtime-editable settings (bootstrap defaults come from .env, then live in DB).
    "setting_channel_url": settings.REQUIRED_CHANNEL_URL,
    "setting_channel_name": settings.REQUIRED_CHANNEL_NAME,
    "setting_channel_id": str(settings.REQUIRED_CHANNEL_ID),
    "setting_giveaway_post_url": settings.GIVEAWAY_POST_URL,
    "setting_specialist_chat_id": settings.SPECIALIST_CHAT_ID,
    "setting_calculation_keyword": settings.CALCULATION_KEYWORD,
    "setting_require_join_approval": "false",
    "setting_unsubscribe_reminder_minutes": "30",
}

SETTINGS_KEYS = [
    "setting_channel_url",
    "setting_channel_name",
    "setting_channel_id",
    "setting_giveaway_post_url",
    "setting_specialist_chat_id",
    "setting_calculation_keyword",
    "setting_require_join_approval",
    "setting_unsubscribe_reminder_minutes",
]

# Человекочитаемые названия для списка в админке (Контент/Настройки),
# чтобы не приходилось разбираться в технических ключах.
CONTENT_LABELS: dict[str, str] = {
    "start_message": "👋 Приветствие (/start)",
    "subscription_message": "📢 Просьба подписаться на канал",
    "subscribed_message": "✅ Спасибо за подписку",
    "why_message": "❓ Зачем нужна инструкция",
    "instruction_message": "📋 Инструкция — вступление",
    "alpha_bank_instruction": "🏦 Как получить выписку в банке (текст + фото)",
    "pdf_instruction": "📄 Инструкция по отправке PDF (текст + файл)",
    "pdf_video_instruction": "🎥 Видео-инструкция по отправке файла",
    "specialist_message": "✍️ Приглашение написать специалисту",
    "giveaway_message": "🎁 Текст розыгрыша",
    "ticket_pending_amount_message": "❓ Сумма не определена — предложить специалиста",
    "reminder_user_message": "⏰ Напоминание неактивному пользователю",
    "unsubscribe_reminder_message": "📉 Напоминание после отписки от канала",
    "setting_channel_url": "🔗 Ссылка на канал",
    "setting_channel_name": "📛 Название канала",
    "setting_channel_id": "🆔 ID канала для проверки подписки",
    "setting_giveaway_post_url": "🎁 Ссылка на пост розыгрыша (по умолчанию)",
    "setting_specialist_chat_id": "💬 Доп. чат для уведомлений специалисту",
    "setting_calculation_keyword": "🔍 Ключевое слово для расчёта переплаты",
    "setting_require_join_approval": "✅ Канал требует одобрения вступления",
    "setting_unsubscribe_reminder_minutes": "⏱ Напоминание после отписки, мин.",
}


def content_label(key: str) -> str:
    return CONTENT_LABELS.get(key, key)


class ContentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContentRepository(session)

    async def seed_defaults(self) -> None:
        existing = {c.key for c in await self.repo.list_all()}
        for key, text in DEFAULT_CONTENT.items():
            if key not in existing:
                await self.repo.upsert(key, text=text)

    async def get_text(self, key: str, **format_kwargs: str) -> str:
        content = await self.repo.get(key)
        text = content.text if content and content.text else DEFAULT_CONTENT.get(key, "")
        if format_kwargs:
            try:
                return text.format(**format_kwargs)
            except (KeyError, IndexError):
                return text
        return text

    async def get_media(self, key: str) -> tuple[str | None, str | None]:
        content = await self.repo.get(key)
        if content is None:
            return None, None
        return content.media_type, content.media_file_id

    async def set_text(self, key: str, text: str, updated_by: int) -> None:
        await self.repo.upsert(key, text=text, updated_by=updated_by)

    async def set_media(self, key: str, media_type: str, media_file_id: str, updated_by: int) -> None:
        await self.repo.upsert(key, media_type=media_type, media_file_id=media_file_id, updated_by=updated_by)

    async def list_all(self) -> list:
        return await self.repo.list_all()

    async def list_text_content(self) -> list:
        return [c for c in await self.repo.list_all() if c.key not in SETTINGS_KEYS]

    async def list_settings(self) -> list:
        return [c for c in await self.repo.list_all() if c.key in SETTINGS_KEYS]

    async def get_channel_url(self) -> str:
        return await self.get_text("setting_channel_url")

    async def get_channel_name(self) -> str:
        return await self.get_text("setting_channel_name")

    async def get_channel_id(self) -> int | str:
        """
        Chat ID для проверки подписки (getChatMember). Для публичных каналов
        это обычно "@username", для остальных - числовой ID. Meняется вместе
        со ссылкой на канал через set_channel_url() при возможности.
        """
        value = (await self.get_text("setting_channel_id")).strip()
        if not value:
            return settings.REQUIRED_CHANNEL_ID
        if value.startswith("@"):
            return value
        try:
            return int(value)
        except ValueError:
            return settings.REQUIRED_CHANNEL_ID

    async def set_channel_id(self, value: int | str, updated_by: int) -> None:
        await self.set_text("setting_channel_id", str(value), updated_by=updated_by)

    async def set_channel_url(self, url: str, updated_by: int) -> str | None:
        """
        Обновляет ссылку на канал. Если это обычная публичная ссылка вида
        t.me/username - заодно переключает ID канала для проверки подписки
        на этот же канал (возвращает username при таком авто-переключении).
        Для приватных ссылок ID канала нужно обновить отдельно вручную.
        """
        from app.utils.telegram_links import parse_channel_username

        await self.set_text("setting_channel_url", url, updated_by=updated_by)
        username = parse_channel_username(url)
        if username:
            await self.set_channel_id(f"@{username}", updated_by=updated_by)
        return username

    async def get_require_join_approval(self) -> bool:
        value = (await self.get_text("setting_require_join_approval")).strip().lower()
        return value in {"true", "1", "да", "yes"}

    async def set_require_join_approval(self, value: bool, updated_by: int) -> None:
        await self.set_text("setting_require_join_approval", "true" if value else "false", updated_by=updated_by)

    async def get_unsubscribe_reminder_minutes(self) -> int:
        value = (await self.get_text("setting_unsubscribe_reminder_minutes")).strip()
        try:
            minutes = int(value)
            return minutes if minutes > 0 else 30
        except ValueError:
            return 30

    async def get_giveaway_post_url(self) -> str:
        return await self.get_text("setting_giveaway_post_url")

    async def get_specialist_chat_id(self) -> int | None:
        value = (await self.get_text("setting_specialist_chat_id")).strip()
        return int(value) if value else None

    async def get_calculation_keyword(self) -> str:
        value = (await self.get_text("setting_calculation_keyword")).strip()
        return value or settings.CALCULATION_KEYWORD

    async def get_subscription_text(self) -> str:
        channel_name = await self.get_channel_name()
        return await self.get_text("subscription_message", channel_name=channel_name)
