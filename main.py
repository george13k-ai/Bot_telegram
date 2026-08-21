from __future__ import annotations

import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError, TelegramRetryAfter
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError

from app.admin.handlers import admin_router
from app.bot.handlers import user_router
from app.bot.middlewares.db_middleware import DbSessionMiddleware
from app.bot.middlewares.throttling import ThrottlingMiddleware
from app.bot.middlewares.user_middleware import UserActivityMiddleware
from app.config import settings
from app.database.session import get_session
from app.services import scheduler as scheduler_service
from app.services.content import ContentService
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def seed_defaults() -> None:
    async with get_session() as session:
        content = ContentService(session)
        await content.seed_defaults()
        await session.commit()


async def start_health_check_server():
    """
    Некоторые бесплатные PaaS-платформы (Render, Railway и т.п.) ожидают, что
    процесс слушает HTTP-порт $PORT, и убивают/усыпляют инстанс, если порт не
    открыт. На обычном VPS/Docker Compose переменная PORT не задаётся, и этот
    сервер просто не запускается - на основной сценарий (long polling) это
    никак не влияет.
    """
    port = os.environ.get("PORT")
    if not port:
        return None

    from aiohttp import web

    app = web.Application()
    app.router.add_get("/", lambda request: web.Response(text="ok"))
    app.router.add_get("/health", lambda request: web.Response(text="ok"))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(port))
    await site.start()
    logger.info("health_check_server_started", port=port)
    return runner


def register_middlewares(dp: Dispatcher) -> None:
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(DbSessionMiddleware())
        observer.outer_middleware(UserActivityMiddleware())
        observer.middleware(ThrottlingMiddleware())


def register_error_handlers(dp: Dispatcher) -> None:
    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        exc = event.exception
        if isinstance(exc, TelegramRetryAfter):
            logger.warning("telegram_retry_after", retry_after=exc.retry_after)
            await asyncio.sleep(exc.retry_after)
            return True
        if isinstance(exc, TelegramForbiddenError):
            logger.info("telegram_forbidden", error=str(exc))
            return True
        if isinstance(exc, (TelegramBadRequest, TelegramNetworkError)):
            logger.warning("telegram_error", error=str(exc))
            return True
        if isinstance(exc, SQLAlchemyError):
            logger.error("database_error", error=str(exc))
            return True
        logger.exception("unhandled_error", error=str(exc))
        return True


async def main() -> None:
    configure_logging()
    await seed_defaults()

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    redis = Redis.from_url(settings.REDIS_URL)
    storage = RedisStorage(redis=redis)

    dp = Dispatcher(storage=storage)
    register_middlewares(dp)
    register_error_handlers(dp)

    dp.include_router(admin_router)
    dp.include_router(user_router)

    scheduler_service.set_bot(bot)
    scheduler = scheduler_service.create_scheduler()
    scheduler_service.register_periodic_jobs(scheduler)
    scheduler.start()

    health_runner = await start_health_check_server()

    logger.info("bot_starting")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, scheduler=scheduler)
    finally:
        scheduler.shutdown(wait=False)
        if health_runner is not None:
            await health_runner.cleanup()
        await bot.session.close()
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
