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
        "Альфа Банк\n\n"
        "Картинка с инструкцией как получить выписку.\n"
        "Просить у Банка банковские платежи по кредиту или кредитной карте за весь "
        "период с момента активации кредитной карты"
    ),
    "pdf_instruction": (
        "Видео инструкции как отправить файл боту!\n"
        "❗ ВАЖНО ❗\n"
        "Пришлите файл PDF в этот чат.\n\n"
        "Если не получится, вы можете написать специалисту."
    ),
    "specialist_message": "Напишите ваше сообщение специалисту, он ответит вам в ближайшее время.",
    "giveaway_message": (
        "Участвуй в бесплатном розыгрыше!\n\n"
        "Каждый месяц 3 машины, 25 новых iPhone 17 pro и 250 человек получат по 20.000 рублей"
    ),
    "giveaway_post_message": (
        "Чтобы участвовать в розыгрыше, отправь репост нашего поста к себе на страницу "
        "или в историю, а затем нажми «Участвовать»."
    ),
    "ticket_pending_amount_message": (
        "Если бот не смог самостоятельно понять сколько можно вернуть и отправить ваши "
        "данные, мы можем отправить заявку специалисту."
    ),
    "reminder_user_message": (
        "Не получилось получить файл от банка? Я могу помочь — просто напиши специалисту, "
        "и мы разберёмся вместе."
    ),
    # Runtime-editable settings (bootstrap defaults come from .env, then live in DB).
    "setting_channel_url": settings.REQUIRED_CHANNEL_URL,
    "setting_channel_name": settings.REQUIRED_CHANNEL_NAME,
    "setting_giveaway_post_url": settings.GIVEAWAY_POST_URL,
    "setting_specialist_chat_id": settings.SPECIALIST_CHAT_ID,
    "setting_calculation_keyword": settings.CALCULATION_KEYWORD,
}

SETTINGS_KEYS = [
    "setting_channel_url",
    "setting_channel_name",
    "setting_giveaway_post_url",
    "setting_specialist_chat_id",
    "setting_calculation_keyword",
]


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
