import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import BabyIncubatorAssignment
from app.models.baby import Baby
from app.models.incubator import Incubator
from app.models.monitoring import MonitoringRecord
from app.models.parent import Parent


class BabyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_active(self) -> list[Baby]:
        result = await self.db.execute(
            select(Baby)
            .where(Baby.is_active == True)
            .options(
                selectinload(Baby.assignments.and_(
                    BabyIncubatorAssignment.status == "active"
                )).selectinload(BabyIncubatorAssignment.incubator),
                selectinload(Baby.assignments.and_(
                    BabyIncubatorAssignment.status == "active"
                )).selectinload(BabyIncubatorAssignment.assigned_by_user),
            )
            .order_by(Baby.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, baby_id: uuid.UUID) -> Baby | None:
        result = await self.db.execute(
            select(Baby)
            .where(Baby.baby_id == baby_id)
            .options(
                selectinload(Baby.parent),
                selectinload(Baby.assignments.and_(
                    BabyIncubatorAssignment.status == "active"
                )).selectinload(BabyIncubatorAssignment.incubator),
                selectinload(Baby.assignments.and_(
                    BabyIncubatorAssignment.status == "active"
                )).selectinload(BabyIncubatorAssignment.assigned_by_user),
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_monitoring(self, baby_id: uuid.UUID) -> MonitoringRecord | None:
        result = await self.db.execute(
            select(MonitoringRecord)
            .where(MonitoringRecord.baby_id == baby_id)
            .order_by(MonitoringRecord.observation_time.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, baby: Baby) -> Baby:
        self.db.add(baby)
        await self.db.flush()
        await self.db.refresh(baby)
        return baby

    async def update(self, baby: Baby) -> Baby:
        await self.db.flush()
        await self.db.refresh(baby)
        return baby
