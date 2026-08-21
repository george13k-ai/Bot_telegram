from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str

    DATABASE_URL: str
    DATABASE_URL_SYNC: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"

    ADMIN_IDS: str = ""
    ADMIN_SECRET_KEY: str = ""

    REQUIRED_CHANNEL_ID: int
    REQUIRED_CHANNEL_URL: str
    REQUIRED_CHANNEL_NAME: str = "Страх Банкира"

    SPECIALIST_CHAT_ID: str = ""

    GIVEAWAY_POST_URL: str = ""

    REMINDER_DELAY_SECONDS: int = 300
    MAX_REMINDERS: int = 3

    MAX_FILE_SIZE_MB: int = 20

    # Ключевое слово для поиска платежей в загруженной PDF-выписке при расчёте
    # переплаты (ТЗ п.13). Настраиваемо и редактируется в админке (Настройки).
    CALCULATION_KEYWORD: str = "страх"

    LOG_LEVEL: str = "INFO"
    TIMEZONE: str = "Europe/Moscow"

    @property
    def admin_ids(self) -> set[int]:
        return {int(x) for x in self.ADMIN_IDS.replace(" ", "").split(",") if x}

    @property
    def specialist_chat_id(self) -> int | None:
        value = self.SPECIALIST_CHAT_ID.strip()
        return int(value) if value else None

    @property
    def database_url_sync(self) -> str:
        if self.DATABASE_URL_SYNC:
            return self.DATABASE_URL_SYNC
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()
