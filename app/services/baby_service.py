import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import BabyIncubatorAssignment
from app.models.baby import Baby
from app.models.parent import Parent
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.baby_repository import BabyRepository
from app.repositories.incubator_repository import IncubatorRepository
from app.schemas.baby import (
    AssignmentInfo,
    BabyCreate,
    BabyDetailResponse,
    BabyResponse,
    BabyUpdate,
    MonitoringSummary,
    ParentResponse,
)
from app.services.audit_service import log_action
from app.services.monitoring_service import _check_vital_status


def _age_in_days(birth_date: date) -> int:
    return (date.today() - birth_date).days


async def register_baby(
    data: BabyCreate,
    db: AsyncSession,
    actor_id: uuid.UUID,
    ip: str | None = None,
) -> BabyDetailResponse:
    inc_repo = IncubatorRepository(db)
    incubator = await inc_repo.get_by_id(data.incubator_id)

    if not incubator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inkubator tidak ditemukan")
    if incubator.status != "kosong":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Inkubator {incubator.incubator_no} tidak tersedia (status: {incubator.status})",
        )

    # check no active assignment already on this incubator (double safety)
    existing = await AssignmentRepository(db).get_active_by_incubator(data.incubator_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inkubator sudah terisi")

    # create baby
    baby = Baby(
        baby_name=data.baby_name,
        gender=data.gender,
        birth_date=data.birth_date,
        birth_weight=data.birth_weight,
        birth_length=data.birth_length,
        gestational_age=data.gestational_age,
        birth_type=data.birth_type,
        clinical_notes=data.clinical_notes,
    )
    baby_repo = BabyRepository(db)
    baby = await baby_repo.create(baby)

    # create parent record
    parent = Parent(
        baby_id=baby.baby_id,
        mother_name=data.parent.mother_name,
        father_name=data.parent.father_name,
        mother_phone=data.parent.mother_phone,
        mother_medical_history=data.parent.mother_medical_history,
        birth_history=data.parent.birth_history,
        delivery_history=data.parent.delivery_history,
        additional_notes=data.parent.additional_notes,
    )
    db.add(parent)
    await db.flush()

    # create assignment
    assignment = BabyIncubatorAssignment(
        baby_id=baby.baby_id,
        incubator_id=data.incubator_id,
        assigned_by=actor_id,
        status="active",
    )
    assignment = await AssignmentRepository(db).create(assignment)

    # update incubator status
    incubator.status = "terisi"
    await inc_repo.update(incubator)

    await log_action(
        db,
        user_id=actor_id,
        action="CREATE",
        table_name="babies",
        record_id=baby.baby_id,
        ip_address=ip,
        details={"baby_name": baby.baby_name, "incubator_no": incubator.incubator_no},
    )

    # reload with relationships
    baby = await baby_repo.get_by_id(baby.baby_id)
    return await _to_detail(baby, db)


async def get_all_babies(db: AsyncSession) -> list[BabyResponse]:
    babies = await BabyRepository(db).get_all_active()
    return [BabyResponse.model_validate(b) for b in babies]


async def get_baby(baby_id: uuid.UUID, db: AsyncSession) -> BabyDetailResponse:
    baby = await BabyRepository(db).get_by_id(baby_id)
    if not baby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data bayi tidak ditemukan")
    return await _to_detail(baby, db)


async def update_baby(
    baby_id: uuid.UUID,
    data: BabyUpdate,
    db: AsyncSession,
    actor_id: uuid.UUID,
    ip: str | None = None,
) -> BabyDetailResponse:
    repo = BabyRepository(db)
    baby = await repo.get_by_id(baby_id)
    if not baby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data bayi tidak ditemukan")

    if data.baby_name is not None:
        baby.baby_name = data.baby_name
    if data.clinical_notes is not None:
        baby.clinical_notes = data.clinical_notes
    if data.birth_weight is not None:
        baby.birth_weight = data.birth_weight

    await repo.update(baby)
    await log_action(db, user_id=actor_id, action="UPDATE", table_name="babies", record_id=baby_id, ip_address=ip)
    baby = await repo.get_by_id(baby_id)
    return await _to_detail(baby, db)


async def discharge_baby(
    baby_id: uuid.UUID,
    db: AsyncSession,
    actor_id: uuid.UUID,
    ip: str | None = None,
) -> None:
    baby_repo = BabyRepository(db)
    baby = await baby_repo.get_by_id(baby_id)
    if not baby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data bayi tidak ditemukan")

    assignment = await AssignmentRepository(db).get_active_by_baby(baby_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bayi tidak sedang dalam inkubator")

    # close assignment
    assignment.status = "discharged"
    assignment.discharged_at = datetime.now(timezone.utc)
    await AssignmentRepository(db).update(assignment)

    # free the incubator
    assignment.incubator.status = "kosong"
    await IncubatorRepository(db).update(assignment.incubator)

    # deactivate baby record
    baby.is_active = False
    await baby_repo.update(baby)

    await log_action(
        db, user_id=actor_id, action="DISCHARGE", table_name="babies",
        record_id=baby_id, ip_address=ip,
        details={"incubator_no": assignment.incubator.incubator_no},
    )


async def _to_detail(baby: Baby, db: AsyncSession) -> BabyDetailResponse:
    active = next((a for a in baby.assignments if a.status == "active"), None)

    assignment_info = None
    if active:
        assignment_info = AssignmentInfo(
            assignment_id=active.assignment_id,
            incubator_id=active.incubator_id,
            incubator_no=active.incubator.incubator_no,
            location=active.incubator.location,
            assigned_at=active.assigned_at,
            assigned_by_name=active.assigned_by_user.full_name if active.assigned_by_user else None,
        )

    latest = await BabyRepository(db).get_latest_monitoring(baby.baby_id)
    latest_vitals = None
    if latest:
        latest_vitals = MonitoringSummary(
            monitoring_id=latest.monitoring_id,
            observation_time=latest.observation_time,
            suhu_bayi=latest.suhu_bayi,
            suhu_inkubator=latest.suhu_inkubator,
            kelembapan_inkubator=latest.kelembapan_inkubator,
            heart_rate=latest.heart_rate,
            respiratory_rate=latest.respiratory_rate,
            spo2=latest.spo2,
            expression_score=latest.expression_score,
            movement_score=latest.movement_score,
            pain_score=latest.pain_score,
            sleep_duration_min=latest.sleep_duration_min,
            sleep_quality=latest.sleep_quality,
            agitation_episodes=latest.agitation_episodes,
            catatan=latest.catatan,
            foto_url=latest.foto_url,
            vital_status=_check_vital_status(
                latest.heart_rate, latest.spo2, latest.suhu_bayi,
                latest.respiratory_rate, latest.pain_score,
            ),
        )

    return BabyDetailResponse(
        baby_id=baby.baby_id,
        baby_name=baby.baby_name,
        gender=baby.gender,
        birth_date=baby.birth_date,
        birth_weight=baby.birth_weight,
        birth_length=baby.birth_length,
        gestational_age=baby.gestational_age,
        birth_type=baby.birth_type,
        clinical_notes=baby.clinical_notes,
        is_active=baby.is_active,
        created_at=baby.created_at,
        age_in_days=_age_in_days(baby.birth_date),
        parent=ParentResponse.model_validate(baby.parent) if baby.parent else None,
        current_assignment=assignment_info,
        latest_vitals=latest_vitals,
    )
