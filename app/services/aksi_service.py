import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aksi import AksiRecord
from app.repositories.aksi_repository import AksiRepository
from app.repositories.baby_repository import BabyRepository
from app.schemas.aksi import (
    AksiCatalog,
    AksiCreate,
    AksiResponse,
    AksiSummary,
    AlarmItem,
    CatalogItem,
    ItemScore,
)
from app.services.aksi_catalog import (
    CATALOG,
    MAX_PER_ITEM,
    MAX_TOTAL,
    PILLAR_KEY,
    PILLAR_LABEL,
    TOTAL_ITEMS,
    category_for,
)
from app.services.audit_service import log_action


def _compute(scores: dict[str, int]):
    """Return (total_score, percentage, category, items, alarms) from raw scores."""
    items: list[ItemScore] = []
    total = 0
    alarms: list[AlarmItem] = []
    for item in CATALOG:
        code = item["item_code"]
        s = scores.get(code)
        raw = int(s) if s is not None else 0
        total += raw
        items.append(ItemScore(
            item_code=code, text=item["text"], score=raw, max=MAX_PER_ITEM,
            percentage=round(raw / MAX_PER_ITEM * 100, 1),
        ))
        if s is not None and s <= 1:
            alarms.append(AlarmItem(item_code=code, text=item["text"], score=int(s)))

    percentage = round(total / MAX_TOTAL * 100, 1) if MAX_TOTAL else 0.0
    category = category_for(percentage)
    return total, percentage, category, items, alarms


def _to_response(record: AksiRecord) -> AksiResponse:
    scores = dict(record.scores or {})
    total, percentage, category, items, alarms = _compute(scores)
    return AksiResponse(
        aksi_id=record.aksi_id,
        baby_id=record.baby_id,
        recorded_by=record.recorded_by,
        recorder_name=record.recorder.full_name if record.recorder else None,
        observation_time=record.observation_time,
        scores=scores,
        catatan=record.catatan,
        total_score=total,
        max_total=MAX_TOTAL,
        percentage=percentage,
        category=category,
        items=items,
        alarms=alarms,
        created_at=record.created_at,
    )


async def create_aksi(
    baby_id: uuid.UUID,
    data: AksiCreate,
    db: AsyncSession,
    actor_id: uuid.UUID,
    ip: str | None = None,
) -> AksiResponse:
    baby = await BabyRepository(db).get_by_id(baby_id)
    if not baby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data bayi tidak ditemukan")

    total, percentage, category, _, alarms = _compute(data.scores)

    record = AksiRecord(
        baby_id=baby_id,
        recorded_by=actor_id,
        observation_time=data.observation_time,
        scores=data.scores,
        catatan=data.catatan,
        total_score=total,
        percentage=percentage,
        category=category,
    )
    repo = AksiRepository(db)
    record = await repo.create(record)

    await log_action(
        db,
        user_id=actor_id,
        action="CREATE",
        table_name="aksi_records",
        record_id=record.aksi_id,
        ip_address=ip,
        details={"percentage": percentage, "category": category, "alarms": len(alarms)},
    )

    record = await repo.get_by_id(record.aksi_id)
    return _to_response(record)


async def list_aksi(
    baby_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> list[AksiResponse]:
    records = await AksiRepository(db).get_by_baby(baby_id, skip=skip, limit=limit)
    return [_to_response(r) for r in records]


async def get_aksi_summary(baby_id: uuid.UUID, db: AsyncSession) -> AksiSummary:
    repo = AksiRepository(db)
    stats = await repo.get_summary_stats(baby_id)
    records = await repo.get_by_baby(baby_id, limit=1)
    latest = records[0] if records else None
    latest_pct = float(latest.percentage) if latest and latest.percentage is not None else None

    return AksiSummary(
        total_sessions=stats["total"],
        avg_percentage=round(stats["avg_percentage"], 1) if stats["avg_percentage"] else None,
        latest_percentage=latest_pct,
        latest_category=category_for(latest_pct) if latest_pct is not None else None,
    )


def get_catalog() -> AksiCatalog:
    return AksiCatalog(
        key=PILLAR_KEY,
        label=PILLAR_LABEL,
        items=[CatalogItem(item_code=c["item_code"], text=c["text"]) for c in CATALOG],
        total_items=TOTAL_ITEMS,
        max_total=MAX_TOTAL,
    )
