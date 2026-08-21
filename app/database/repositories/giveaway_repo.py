from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.giveaway import Giveaway, GiveawayParticipant


class GiveawayRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active(self) -> Giveaway | None:
        stmt = (
            select(Giveaway)
            .where(Giveaway.is_active.is_(True))
            .order_by(Giveaway.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, giveaway_id: int) -> Giveaway | None:
        return await self.session.get(Giveaway, giveaway_id)

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Giveaway]:
        stmt = select(Giveaway).order_by(Giveaway.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        title: str,
        description: str | None,
        image_file_id: str | None = None,
        is_active: bool = True,
    ) -> Giveaway:
        giveaway = Giveaway(
            title=title, description=description, image_file_id=image_file_id, is_active=is_active
        )
        self.session.add(giveaway)
        await self.session.flush()
        return giveaway

    async def set_active(self, giveaway: Giveaway, is_active: bool) -> None:
        giveaway.is_active = is_active

    async def is_participant(self, giveaway_id: int, user_id: int) -> bool:
        stmt = select(GiveawayParticipant).where(
            GiveawayParticipant.giveaway_id == giveaway_id, GiveawayParticipant.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_participant(self, giveaway_id: int, user_id: int) -> GiveawayParticipant | None:
        if await self.is_participant(giveaway_id, user_id):
            return None
        participant = GiveawayParticipant(giveaway_id=giveaway_id, user_id=user_id)
        self.session.add(participant)
        await self.session.flush()
        return participant

    async def count_participants(self, giveaway_id: int) -> int:
        result = await self.session.execute(
            select(func.count(GiveawayParticipant.id)).where(GiveawayParticipant.giveaway_id == giveaway_id)
        )
        return result.scalar_one()

    async def count_all_participants(self) -> int:
        result = await self.session.execute(select(func.count(GiveawayParticipant.id)))
        return result.scalar_one()
