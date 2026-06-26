import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.involvement import ParentInvolvementRecord


class InvolvementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_baby(
        self,
        baby_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ParentInvolvementRecord]:
        result = await self.db.execute(
            select(ParentInvolvementRecord)
            .where(ParentInvolvementRecord.baby_id == baby_id)
            .options(selectinload(ParentInvolvementRecord.recorder))
            .order_by(ParentInvolvementRecord.observation_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_by_baby(self, baby_id: uuid.UUID) -> list[ParentInvolvementRecord]:
        result = await self.db.execute(
            select(ParentInvolvementRecord)
            .where(ParentInvolvementRecord.baby_id == baby_id)
            .options(selectinload(ParentInvolvementRecord.recorder))
            .order_by(ParentInvolvementRecord.observation_time.desc())
        )
        return list(result.scalars().all())

    async def get_summary_stats(self, baby_id: uuid.UUID) -> dict:
        result = await self.db.execute(
            select(
                func.count(ParentInvolvementRecord.involvement_id).label("total"),
                func.avg(ParentInvolvementRecord.skor_keterlibatan).label("avg_skor"),
                func.avg(ParentInvolvementRecord.durasi_menyusui).label("avg_menyusui"),
                func.avg(ParentInvolvementRecord.durasi_interaksi).label("avg_interaksi"),
            ).where(ParentInvolvementRecord.baby_id == baby_id)
        )
        row = result.one()
        return {
            "total": row.total or 0,
            "avg_skor": float(row.avg_skor) if row.avg_skor else None,
            "avg_menyusui": float(row.avg_menyusui) if row.avg_menyusui else None,
            "avg_interaksi": float(row.avg_interaksi) if row.avg_interaksi else None,
        }

    async def create(self, record: ParentInvolvementRecord) -> ParentInvolvementRecord:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record
