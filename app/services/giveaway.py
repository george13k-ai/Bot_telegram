from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.giveaway import Giveaway
from app.database.repositories.giveaway_repo import GiveawayRepository


class GiveawayJoinResult:
    def __init__(self, joined: bool, already_participant: bool) -> None:
        self.joined = joined
        self.already_participant = already_participant


class GiveawayService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GiveawayRepository(session)

    async def get_active(self) -> Giveaway | None:
        return await self.repo.get_active()

    async def get_by_id(self, giveaway_id: int) -> Giveaway | None:
        return await self.repo.get_by_id(giveaway_id)

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Giveaway]:
        return await self.repo.list_all(limit, offset)

    async def create(self, title: str, description: str | None, image_file_id: str | None = None) -> Giveaway:
        return await self.repo.create(title, description, image_file_id)

    async def set_active(self, giveaway: Giveaway, is_active: bool) -> None:
        await self.repo.set_active(giveaway, is_active)

    async def is_participant(self, giveaway_id: int, user_id: int) -> bool:
        return await self.repo.is_participant(giveaway_id, user_id)

    async def join(self, giveaway_id: int, user_id: int) -> GiveawayJoinResult:
        if await self.repo.is_participant(giveaway_id, user_id):
            return GiveawayJoinResult(joined=False, already_participant=True)
        try:
            participant = await self.repo.add_participant(giveaway_id, user_id)
        except IntegrityError:
            await self.session.rollback()
            return GiveawayJoinResult(joined=False, already_participant=True)
        return GiveawayJoinResult(joined=participant is not None, already_participant=participant is None)

    async def count_participants(self, giveaway_id: int) -> int:
        return await self.repo.count_participants(giveaway_id)

    async def count_all_participants(self) -> int:
        return await self.repo.count_all_participants()
