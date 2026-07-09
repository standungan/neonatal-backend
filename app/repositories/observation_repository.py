import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.observation import Observation


class ObservationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_baby(
        self,
        baby_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Observation]:
        result = await self.db.execute(
            select(Observation)
            .where(Observation.baby_id == baby_id)
            .options(selectinload(Observation.recorder))
            .order_by(Observation.observation_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, observation_id: uuid.UUID) -> Observation | None:
        result = await self.db.execute(
            select(Observation)
            .where(Observation.observation_id == observation_id)
            .options(selectinload(Observation.recorder))
        )
        return result.scalar_one_or_none()

    async def create(self, record: Observation) -> Observation:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record
