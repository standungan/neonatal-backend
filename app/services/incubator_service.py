import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incubator import Incubator
from app.repositories.incubator_repository import IncubatorRepository
from app.schemas.incubator import (
    CurrentBabySummary,
    IncubatorCreate,
    IncubatorDetailResponse,
    IncubatorResponse,
    IncubatorUpdate,
)
from app.services.audit_service import log_action


async def get_all_incubators(db: AsyncSession) -> list[IncubatorDetailResponse]:
    repo = IncubatorRepository(db)
    incubators = await repo.get_all_with_assignment()
    return [_to_detail_response(inc) for inc in incubators]


async def get_incubator(incubator_id: uuid.UUID, db: AsyncSession) -> IncubatorDetailResponse:
    repo = IncubatorRepository(db)
    inc = await repo.get_by_id_with_assignment(incubator_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inkubator tidak ditemukan")
    return _to_detail_response(inc)


async def get_available_incubators(db: AsyncSession) -> list[IncubatorResponse]:
    repo = IncubatorRepository(db)
    incubators = await repo.get_available()
    return [IncubatorResponse.model_validate(i) for i in incubators]


async def create_incubator(
    data: IncubatorCreate,
    db: AsyncSession,
    actor_id: uuid.UUID | None = None,
    ip: str | None = None,
) -> IncubatorResponse:
    repo = IncubatorRepository(db)

    if await repo.number_exists(data.incubator_no):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inkubator nomor {data.incubator_no} sudah ada",
        )

    inc = Incubator(incubator_no=data.incubator_no, location=data.location)
    inc = await repo.create(inc)

    await log_action(
        db,
        user_id=actor_id,
        action="CREATE",
        table_name="incubators",
        record_id=inc.incubator_id,
        ip_address=ip,
        details={"incubator_no": inc.incubator_no},
    )
    return IncubatorResponse.model_validate(inc)


async def update_incubator(
    incubator_id: uuid.UUID,
    data: IncubatorUpdate,
    db: AsyncSession,
    actor_id: uuid.UUID | None = None,
    ip: str | None = None,
) -> IncubatorResponse:
    repo = IncubatorRepository(db)
    inc = await repo.get_by_id(incubator_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inkubator tidak ditemukan")

    if data.location is not None:
        inc.location = data.location
    if data.status is not None:
        inc.status = data.status

    inc = await repo.update(inc)

    await log_action(
        db,
        user_id=actor_id,
        action="UPDATE",
        table_name="incubators",
        record_id=incubator_id,
        ip_address=ip,
    )
    return IncubatorResponse.model_validate(inc)


def _to_detail_response(inc: Incubator) -> IncubatorDetailResponse:
    active = next((a for a in inc.assignments if a.status == "active"), None)
    current_baby = None
    if active and active.baby:
        current_baby = CurrentBabySummary(
            baby_id=active.baby.baby_id,
            baby_name=active.baby.baby_name,
            birth_date=active.baby.birth_date,
            assigned_at=active.assigned_at,
        )
    return IncubatorDetailResponse(
        incubator_id=inc.incubator_id,
        incubator_no=inc.incubator_no,
        location=inc.location,
        status=inc.status,
        created_at=inc.created_at,
        updated_at=inc.updated_at,
        current_baby=current_baby,
    )
