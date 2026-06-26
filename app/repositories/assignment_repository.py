import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import BabyIncubatorAssignment


class AssignmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_by_baby(self, baby_id: uuid.UUID) -> BabyIncubatorAssignment | None:
        result = await self.db.execute(
            select(BabyIncubatorAssignment)
            .where(
                BabyIncubatorAssignment.baby_id == baby_id,
                BabyIncubatorAssignment.status == "active",
            )
            .options(selectinload(BabyIncubatorAssignment.incubator))
        )
        return result.scalar_one_or_none()

    async def get_active_by_incubator(self, incubator_id: uuid.UUID) -> BabyIncubatorAssignment | None:
        result = await self.db.execute(
            select(BabyIncubatorAssignment)
            .where(
                BabyIncubatorAssignment.incubator_id == incubator_id,
                BabyIncubatorAssignment.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def create(self, assignment: BabyIncubatorAssignment) -> BabyIncubatorAssignment:
        self.db.add(assignment)
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def update(self, assignment: BabyIncubatorAssignment) -> BabyIncubatorAssignment:
        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment
