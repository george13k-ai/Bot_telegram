from aiogram import Router

from app.admin.handlers import content, giveaways, mailings, menu, notifications, statistics, subscriptions, users
from app.bot.filters.admin_filter import IsAdminFilter

admin_router = Router(name="admin")
admin_router.message.filter(IsAdminFilter())
admin_router.callback_query.filter(IsAdminFilter())

admin_router.include_router(menu.router)
admin_router.include_router(users.router)
admin_router.include_router(mailings.router)
admin_router.include_router(giveaways.router)
admin_router.include_router(subscriptions.router)
admin_router.include_router(notifications.router)
admin_router.include_router(statistics.router)
admin_router.include_router(content.router)

__all__ = ["admin_router"]
