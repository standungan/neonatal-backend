import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.aksi import AksiRecord


class AksiRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_baby(
        self,
        baby_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AksiRecord]:
        result = await self.db.execute(
            select(AksiRecord)
            .where(AksiRecord.baby_id == baby_id)
            .options(selectinload(AksiRecord.recorder))
            .order_by(AksiRecord.observation_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_by_baby(self, baby_id: uuid.UUID) -> list[AksiRecord]:
        result = await self.db.execute(
            select(AksiRecord)
            .where(AksiRecord.baby_id == baby_id)
            .options(selectinload(AksiRecord.recorder))
            .order_by(AksiRecord.observation_time.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, aksi_id: uuid.UUID) -> AksiRecord | None:
        result = await self.db.execute(
            select(AksiRecord)
            .where(AksiRecord.aksi_id == aksi_id)
            .options(selectinload(AksiRecord.recorder))
        )
        return result.scalar_one_or_none()

    async def get_summary_stats(self, baby_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(
                func.count(AksiRecord.aksi_id).label("total"),
                func.avg(AksiRecord.percentage).label("avg_percentage"),
            ).where(AksiRecord.baby_id == baby_id)
        )
        row = result.one()
        return {
            "total": row.total or 0,
            "avg_percentage": float(row.avg_percentage) if row.avg_percentage else None,
        }

    async def create(self, record: AksiRecord) -> AksiRecord:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record
