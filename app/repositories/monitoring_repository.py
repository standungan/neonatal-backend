import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.monitoring import MonitoringRecord


class MonitoringRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_baby(
        self,
        baby_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MonitoringRecord]:
        result = await self.db.execute(
            select(MonitoringRecord)
            .where(MonitoringRecord.baby_id == baby_id)
            .options(selectinload(MonitoringRecord.recorder))
            .order_by(MonitoringRecord.observation_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, monitoring_id: uuid.UUID) -> MonitoringRecord | None:
        result = await self.db.execute(
            select(MonitoringRecord)
            .where(MonitoringRecord.monitoring_id == monitoring_id)
            .options(selectinload(MonitoringRecord.recorder))
        )
        return result.scalar_one_or_none()

    async def create(self, record: MonitoringRecord) -> MonitoringRecord:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def get_all_by_baby(self, baby_id: uuid.UUID) -> list[MonitoringRecord]:
        result = await self.db.execute(
            select(MonitoringRecord)
            .where(MonitoringRecord.baby_id == baby_id)
            .options(selectinload(MonitoringRecord.recorder))
            .order_by(MonitoringRecord.observation_time.desc())
        )
        return list(result.scalars().all())

    async def get_latest_per_baby(
        self, baby_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, MonitoringRecord]:
        """Returns {baby_id: latest_record} for all given baby_ids in one query."""
        if not baby_ids:
            return {}
        # PostgreSQL DISTINCT ON — fastest approach for this pattern
        result = await self.db.execute(
            select(MonitoringRecord)
            .distinct(MonitoringRecord.baby_id)
            .where(MonitoringRecord.baby_id.in_(baby_ids))
            .order_by(MonitoringRecord.baby_id, MonitoringRecord.observation_time.desc())
        )
        return {r.baby_id: r for r in result.scalars().all()}

    async def update(self, record: MonitoringRecord) -> MonitoringRecord:
        await self.db.flush()
        await self.db.refresh(record)
        return record
