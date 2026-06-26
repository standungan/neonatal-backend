import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import BabyIncubatorAssignment
from app.models.incubator import Incubator


class IncubatorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[Incubator]:
        result = await self.db.execute(
            select(Incubator).order_by(Incubator.incubator_no)
        )
        return list(result.scalars().all())

    async def get_all_with_assignment(self) -> list[Incubator]:
        """Load incubators with their active assignment + baby for the dashboard."""
        result = await self.db.execute(
            select(Incubator)
            .options(
                selectinload(Incubator.assignments.and_(
                    BabyIncubatorAssignment.status == "active"
                )).selectinload(BabyIncubatorAssignment.baby)
            )
            .order_by(Incubator.incubator_no)
        )
        return list(result.scalars().all())

    async def get_by_id(self, incubator_id: uuid.UUID) -> Incubator | None:
        result = await self.db.execute(
            select(Incubator).where(Incubator.incubator_id == incubator_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_assignment(self, incubator_id: uuid.UUID) -> Incubator | None:
        result = await self.db.execute(
            select(Incubator)
            .where(Incubator.incubator_id == incubator_id)
            .options(
                selectinload(Incubator.assignments.and_(
                    BabyIncubatorAssignment.status == "active"
                )).selectinload(BabyIncubatorAssignment.baby)
            )
        )
        return result.scalar_one_or_none()

    async def number_exists(self, incubator_no: str, exclude_id: uuid.UUID | None = None) -> bool:
        stmt = select(Incubator.incubator_id).where(Incubator.incubator_no == incubator_no)
        if exclude_id:
            stmt = stmt.where(Incubator.incubator_id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, incubator: Incubator) -> Incubator:
        self.db.add(incubator)
        await self.db.flush()
        await self.db.refresh(incubator)
        return incubator

    async def update(self, incubator: Incubator) -> Incubator:
        await self.db.flush()
        await self.db.refresh(incubator)
        return incubator

    async def get_available(self) -> list[Incubator]:
        """Return incubators that can accept a new baby."""
        result = await self.db.execute(
            select(Incubator)
            .where(Incubator.status == "kosong")
            .order_by(Incubator.incubator_no)
        )
        return list(result.scalars().all())
