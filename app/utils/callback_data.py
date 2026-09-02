from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MainCB(CallbackData, prefix="main"):
    action: str  # yes | giveaway | specialist | home


class SubscriptionCB(CallbackData, prefix="subscription"):
    action: str  # check


class InstructionCB(CallbackData, prefix="instruction"):
    action: str  # get | video


class SpecialistCB(CallbackData, prefix="specialist"):
    action: str  # create | reply_ticket
    ticket_id: int | None = None


class GiveawayCB(CallbackData, prefix="giveaway"):
    action: str  # open | join
    giveaway_id: int | None = None


class AdminMenuCB(CallbackData, prefix="admin"):
    section: str  # users | mailings | giveaways | subscriptions | notifications | statistics | content | settings | home


class AdminUserCB(CallbackData, prefix="admin_user"):
    action: str  # list | search | card | tag_add | tag_remove
    user_id: int | None = None
    page: int = 0
    tag_id: int | None = None


class MailingCB(CallbackData, prefix="mailing"):
    action: str
    mailing_id: int | None = None
    page: int = 0
    tag_id: int | None = None


class NotificationCB(CallbackData, prefix="notif"):
    action: str  # reply
    notification_id: int
    ticket_id: int | None = None
    user_id: int | None = None


class ContentCB(CallbackData, prefix="content"):
    action: str  # list | view | edit_text | edit_media
    key: str = ""


class GiveawayAdminCB(CallbackData, prefix="ga"):
    # list | create | toggle | view | set_photo | img_skip | set_post_url | post_url_skip
    # | delete | delete_confirm | edit_title
    action: str
    giveaway_id: int | None = None
    page: int = 0
