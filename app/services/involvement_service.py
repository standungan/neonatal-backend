import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.involvement import ParentInvolvementRecord
from app.repositories.baby_repository import BabyRepository
from app.repositories.involvement_repository import InvolvementRepository
from app.schemas.involvement import (
    InvolvementCreate,
    InvolvementResponse,
    InvolvementSummary,
)
from app.services.audit_service import log_action

# ── Parent Engagement Index (PEI) ───────────────────────────────────────────────
# Pillar 8 has 8 sub-domains, each rated 0–4 (max raw = 32).
# PEI = round(sum / 32 * 100), giving a 0–100 index.

_DOMAIN_FIELDS = (
    "presence_score",
    "physical_interaction_score",
    "feeding_participation_score",
    "care_participation_score",
    "knowledge_score",
    "communication_score",
    "emotional_readiness_score",
    "discharge_readiness_score",
)
_DOMAIN_MAX = len(_DOMAIN_FIELDS) * 4   # 32

_SCORE_CATEGORIES = [
    (76, "Sangat Baik"),
    (51, "Baik"),
    (26, "Sedang"),
    (0,  "Rendah"),
]


def calculate_score(data) -> int:
    """Compute the Parent Engagement Index (0–100) from the 8 Pillar-8 domains."""
    raw = sum(getattr(data, f) or 0 for f in _DOMAIN_FIELDS)
    return round(raw / _DOMAIN_MAX * 100)


def score_to_category(score: int | None) -> str | None:
    if score is None:
        return None
    for threshold, label in _SCORE_CATEGORIES:
        if score >= threshold:
            return label
    return "Rendah"


def _to_response(record: ParentInvolvementRecord) -> InvolvementResponse:
    return InvolvementResponse(
        involvement_id=record.involvement_id,
        baby_id=record.baby_id,
        recorded_by=record.recorded_by,
        recorder_name=record.recorder.full_name if record.recorder else None,
        observation_time=record.observation_time,
        durasi_menyusui=record.durasi_menyusui,
        durasi_interaksi=record.durasi_interaksi,
        presence_score=record.presence_score,
        physical_interaction_score=record.physical_interaction_score,
        feeding_participation_score=record.feeding_participation_score,
        care_participation_score=record.care_participation_score,
        knowledge_score=record.knowledge_score,
        communication_score=record.communication_score,
        emotional_readiness_score=record.emotional_readiness_score,
        discharge_readiness_score=record.discharge_readiness_score,
        catatan=record.catatan,
        skor_keterlibatan=record.skor_keterlibatan,
        skor_kategori=score_to_category(record.skor_keterlibatan),
        kondisi_bayi=record.kondisi_bayi,
        created_at=record.created_at,
    )


async def create_involvement(
    baby_id: uuid.UUID,
    data: InvolvementCreate,
    db: AsyncSession,
    actor_id: uuid.UUID,
    ip: str | None = None,
) -> InvolvementResponse:
    baby = await BabyRepository(db).get_by_id(baby_id)
    if not baby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data bayi tidak ditemukan")

    skor = calculate_score(data)

    record = ParentInvolvementRecord(
        baby_id=baby_id,
        recorded_by=actor_id,
        observation_time=data.observation_time,
        durasi_menyusui=data.durasi_menyusui,
        durasi_interaksi=data.durasi_interaksi,
        presence_score=data.presence_score,
        physical_interaction_score=data.physical_interaction_score,
        feeding_participation_score=data.feeding_participation_score,
        care_participation_score=data.care_participation_score,
        knowledge_score=data.knowledge_score,
        communication_score=data.communication_score,
        emotional_readiness_score=data.emotional_readiness_score,
        discharge_readiness_score=data.discharge_readiness_score,
        catatan=data.catatan,
        skor_keterlibatan=skor,
        kondisi_bayi=data.kondisi_bayi,
    )

    repo = InvolvementRepository(db)
    record = await repo.create(record)

    await log_action(
        db,
        user_id=actor_id,
        action="CREATE",
        table_name="parent_involvement_records",
        record_id=record.involvement_id,
        ip_address=ip,
        details={"skor": skor, "kategori": score_to_category(skor)},
    )
    return _to_response(record)


async def list_involvement(
    baby_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> list[InvolvementResponse]:
    records = await InvolvementRepository(db).get_by_baby(baby_id, skip=skip, limit=limit)
    return [_to_response(r) for r in records]


async def get_involvement_summary(baby_id: uuid.UUID, db: AsyncSession) -> InvolvementSummary:
    repo = InvolvementRepository(db)
    stats = await repo.get_summary_stats(baby_id)
    records = await repo.get_by_baby(baby_id, limit=1)
    latest = records[0] if records else None

    return InvolvementSummary(
        total_sessions=stats["total"],
        avg_skor=round(stats["avg_skor"], 1) if stats["avg_skor"] else None,
        avg_durasi_menyusui=round(stats["avg_menyusui"], 1) if stats["avg_menyusui"] else None,
        avg_durasi_interaksi=round(stats["avg_interaksi"], 1) if stats["avg_interaksi"] else None,
        latest_skor=latest.skor_keterlibatan if latest else None,
        latest_kategori=score_to_category(latest.skor_keterlibatan) if latest else None,
    )
