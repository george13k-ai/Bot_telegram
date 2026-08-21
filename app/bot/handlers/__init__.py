from aiogram import Router

from app.bot.handlers import giveaway, instruction, pdf_flow, specialist, start, subscription, fallback

user_router = Router(name="user")

user_router.include_router(start.router)
user_router.include_router(subscription.router)
user_router.include_router(instruction.router)
user_router.include_router(specialist.router)
user_router.include_router(giveaway.router)
user_router.include_router(pdf_flow.router)
user_router.include_router(fallback.router)

__all__ = ["user_router"]
