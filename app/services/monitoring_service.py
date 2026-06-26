import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitoring import MonitoringRecord
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.incubator_repository import IncubatorRepository
from app.repositories.monitoring_repository import MonitoringRepository
from app.schemas.monitoring import MonitoringCreate, MonitoringResponse, PhotoUploadResponse
from app.services.audit_service import log_action
from app.services.storage_service import save_photo

# ── Neonatal vital thresholds ──────────────────────────────────────────────────
HR_MIN = 100       # bpm
HR_MAX = 160       # bpm
RR_MIN = 40        # breaths/min
RR_MAX = 60        # breaths/min
SPO2_MIN = 93.0    # %
TEMP_MIN = 36.0    # °C
TEMP_MAX = 37.5    # °C
PAIN_WARN = 4      # NIPS ≥ 4 indicates pain


def _check_vital_status(
    heart_rate: int | None,
    spo2: Decimal | None,
    suhu_bayi: Decimal | None,
    respiratory_rate: int | None = None,
    pain_score: int | None = None,
) -> str:
    if heart_rate and (heart_rate < HR_MIN or heart_rate > HR_MAX):
        return "warning"
    if respiratory_rate and (respiratory_rate < RR_MIN or respiratory_rate > RR_MAX):
        return "warning"
    if spo2 and spo2 < SPO2_MIN:
        return "warning"
    if suhu_bayi and (suhu_bayi < TEMP_MIN or suhu_bayi > TEMP_MAX):
        return "warning"
    if pain_score is not None and pain_score >= PAIN_WARN:
        return "warning"
    return "normal"


def _to_response(record: MonitoringRecord) -> MonitoringResponse:
    return MonitoringResponse(
        monitoring_id=record.monitoring_id,
        baby_id=record.baby_id,
        recorded_by=record.recorded_by,
        recorder_name=record.recorder.full_name if record.recorder else None,
        observation_time=record.observation_time,
        suhu_bayi=record.suhu_bayi,
        suhu_inkubator=record.suhu_inkubator,
        kelembapan_inkubator=record.kelembapan_inkubator,
        heart_rate=record.heart_rate,
        respiratory_rate=record.respiratory_rate,
        spo2=record.spo2,
        expression_score=record.expression_score,
        movement_score=record.movement_score,
        pain_score=record.pain_score,
        sleep_duration_min=record.sleep_duration_min,
        sleep_quality=record.sleep_quality,
        agitation_episodes=record.agitation_episodes,
        catatan=record.catatan,
        foto_url=record.foto_url,
        vital_status=_check_vital_status(
            record.heart_rate, record.spo2, record.suhu_bayi,
            record.respiratory_rate, record.pain_score,
        ),
        created_at=record.created_at,
    )


async def create_monitoring(
    baby_id: uuid.UUID,
    data: MonitoringCreate,
    db: AsyncSession,
    actor_id: uuid.UUID,
    ip: str | None = None,
) -> MonitoringResponse:
    record = MonitoringRecord(
        baby_id=baby_id,
        recorded_by=actor_id,
        observation_time=data.observation_time,
        suhu_bayi=data.suhu_bayi,
        suhu_inkubator=data.suhu_inkubator,
        kelembapan_inkubator=data.kelembapan_inkubator,
        heart_rate=data.heart_rate,
        respiratory_rate=data.respiratory_rate,
        spo2=data.spo2,
        expression_score=data.expression_score,
        movement_score=data.movement_score,
        pain_score=data.pain_score,
        sleep_duration_min=data.sleep_duration_min,
        sleep_quality=data.sleep_quality,
        agitation_episodes=data.agitation_episodes,
        catatan=data.catatan,
    )

    repo = MonitoringRepository(db)
    record = await repo.create(record)

    # update incubator status based on vitals
    vital_status = _check_vital_status(
        data.heart_rate, data.spo2, data.suhu_bayi,
        data.respiratory_rate, data.pain_score,
    )
    assignment = await AssignmentRepository(db).get_active_by_baby(baby_id)
    if assignment:
        new_inc_status = "warning" if vital_status == "warning" else "terisi"
        if assignment.incubator.status != new_inc_status:
            assignment.incubator.status = new_inc_status
            await IncubatorRepository(db).update(assignment.incubator)

    await log_action(
        db,
        user_id=actor_id,
        action="CREATE",
        table_name="monitoring_records",
        record_id=record.monitoring_id,
        ip_address=ip,
    )

    # reload with recorder relationship
    record = await repo.get_by_id(record.monitoring_id)
    return _to_response(record)


async def list_monitoring(
    baby_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> list[MonitoringResponse]:
    records = await MonitoringRepository(db).get_by_baby(baby_id, skip=skip, limit=limit)
    return [_to_response(r) for r in records]


async def upload_photo(
    monitoring_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession,
    actor_id: uuid.UUID,
    ip: str | None = None,
) -> PhotoUploadResponse:
    repo = MonitoringRepository(db)
    record = await repo.get_by_id(monitoring_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data monitoring tidak ditemukan")

    foto_url = await save_photo(file, record.baby_id, monitoring_id)
    record.foto_url = foto_url
    await repo.update(record)

    await log_action(
        db,
        user_id=actor_id,
        action="UPLOAD_PHOTO",
        table_name="monitoring_records",
        record_id=monitoring_id,
        ip_address=ip,
    )
    return PhotoUploadResponse(monitoring_id=monitoring_id, foto_url=foto_url)
