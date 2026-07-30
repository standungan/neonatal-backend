import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.baby_repository import BabyRepository
from app.repositories.involvement_repository import InvolvementRepository
from app.repositories.monitoring_repository import MonitoringRepository
from app.schemas.report import BabyReportResponse
from app.services.aksi_service import list_aksi
from app.services.baby_service import _to_detail
from app.services.involvement_service import _to_response as involvement_to_response
from app.services.involvement_service import get_involvement_summary
from app.services.monitoring_service import _to_response as monitoring_to_response
from app.services.observation_service import list_observations


async def get_baby_report(baby_id: uuid.UUID, db: AsyncSession) -> BabyReportResponse:
    baby = await BabyRepository(db).get_by_id(baby_id)
    if not baby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data bayi tidak ditemukan")

    monitoring_records = await MonitoringRepository(db).get_all_by_baby(baby_id)
    involvement_records = await InvolvementRepository(db).get_all_by_baby(baby_id)
    involvement_summary = await get_involvement_summary(baby_id, db)
    baby_detail = await _to_detail(baby, db)

    # latest 8-pillar assessments (newest first → [0])
    observations = await list_observations(baby_id, db, limit=1)
    aksi = await list_aksi(baby_id, db, limit=1)

    return BabyReportResponse(
        baby=baby_detail,
        monitoring_history=[monitoring_to_response(r) for r in monitoring_records],
        involvement_history=[involvement_to_response(r) for r in involvement_records],
        involvement_summary=involvement_summary,
        observation_latest=observations[0] if observations else None,
        aksi_latest=aksi[0] if aksi else None,
        generated_at=datetime.now(timezone.utc),
    )
