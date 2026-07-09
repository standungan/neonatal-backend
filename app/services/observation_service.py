import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observation import Observation
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.baby_repository import BabyRepository
from app.repositories.incubator_repository import IncubatorRepository
from app.repositories.observation_repository import ObservationRepository
from app.schemas.observation import (
    AlarmItem,
    CatalogItem,
    CatalogPillar,
    ObservationCatalog,
    ObservationCreate,
    ObservationResponse,
    PillarScore,
)
from app.services.audit_service import log_action
from app.services.observation_catalog import (
    CATALOG,
    MAX_PER_ITEM,
    MAX_TOTAL,
    PILLARS,
    TOTAL_ITEMS,
    category_for,
)


def _compute(scores: dict[str, int]):
    """Return (total_score, percentage, category, pillars, alarms) from raw scores."""
    pillars: list[PillarScore] = []
    total = 0
    for p in PILLARS:
        codes = [f"{p['key']}_{i}" for i in range(1, len(p["items"]) + 1)]
        raw = sum(int(scores.get(c, 0)) for c in codes)
        pmax = len(codes) * MAX_PER_ITEM
        total += raw
        pillars.append(PillarScore(
            key=p["key"], label=p["label"], score=raw, max=pmax,
            percentage=round(raw / pmax * 100, 1) if pmax else 0.0,
        ))

    percentage = round(total / MAX_TOTAL * 100, 1) if MAX_TOTAL else 0.0
    category = category_for(percentage)

    alarms: list[AlarmItem] = []
    for item in CATALOG:
        s = scores.get(item["item_code"])
        if s is not None and s <= 1:
            alarms.append(AlarmItem(
                item_code=item["item_code"], text=item["text"],
                pillar_label=item["pillar_label"], score=int(s),
            ))
    return total, percentage, category, pillars, alarms


def _to_response(record: Observation) -> ObservationResponse:
    scores = dict(record.scores or {})
    total, percentage, category, pillars, alarms = _compute(scores)
    return ObservationResponse(
        observation_id=record.observation_id,
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
        pillars=pillars,
        alarms=alarms,
        created_at=record.created_at,
    )


async def create_observation(
    baby_id: uuid.UUID,
    data: ObservationCreate,
    db: AsyncSession,
    actor_id: uuid.UUID,
    ip: str | None = None,
) -> ObservationResponse:
    baby = await BabyRepository(db).get_by_id(baby_id)
    if not baby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data bayi tidak ditemukan")

    total, percentage, category, _, alarms = _compute(data.scores)

    record = Observation(
        baby_id=baby_id,
        recorded_by=actor_id,
        observation_time=data.observation_time,
        scores=data.scores,
        catatan=data.catatan,
        total_score=total,
        percentage=percentage,
        category=category,
    )
    repo = ObservationRepository(db)
    record = await repo.create(record)

    # any item scored 0 = penyimpangan berat → raise incubator to "warning"
    has_critical = any(a.score == 0 for a in alarms)
    if has_critical:
        assignment = await AssignmentRepository(db).get_active_by_baby(baby_id)
        if assignment and assignment.incubator.status not in ("kosong", "tidak_tersedia"):
            if assignment.incubator.status != "warning":
                assignment.incubator.status = "warning"
                await IncubatorRepository(db).update(assignment.incubator)

    await log_action(
        db,
        user_id=actor_id,
        action="CREATE",
        table_name="observations",
        record_id=record.observation_id,
        ip_address=ip,
        details={"percentage": percentage, "category": category, "alarms": len(alarms)},
    )

    record = await repo.get_by_id(record.observation_id)
    return _to_response(record)


async def list_observations(
    baby_id: uuid.UUID,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> list[ObservationResponse]:
    records = await ObservationRepository(db).get_by_baby(baby_id, skip=skip, limit=limit)
    return [_to_response(r) for r in records]


def get_catalog() -> ObservationCatalog:
    pillars = [
        CatalogPillar(
            key=p["key"], label=p["label"],
            items=[
                CatalogItem(item_code=f"{p['key']}_{i}", text=text)
                for i, text in enumerate(p["items"], start=1)
            ],
        )
        for p in PILLARS
    ]
    return ObservationCatalog(pillars=pillars, total_items=TOTAL_ITEMS, max_total=MAX_TOTAL)
