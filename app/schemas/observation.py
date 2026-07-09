import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class ObservationCreate(BaseModel):
    observation_time: datetime
    scores: dict[str, int]        # { item_code: 0-3 }
    catatan: str | None = None

    @field_validator("scores")
    @classmethod
    def scores_in_range(cls, v: dict[str, int]) -> dict[str, int]:
        for code, score in v.items():
            if not isinstance(score, int) or not (0 <= score <= 3):
                raise ValueError(f"Skor '{code}' harus bilangan 0–3")
        return v


class PillarScore(BaseModel):
    key: str
    label: str
    score: int          # raw sum for the pillar
    max: int            # item_count * 3
    percentage: float   # 0–100


class AlarmItem(BaseModel):
    item_code: str
    text: str
    pillar_label: str
    score: int          # 0 or 1


class ObservationResponse(BaseModel):
    observation_id: uuid.UUID
    baby_id: uuid.UUID
    recorded_by: uuid.UUID
    recorder_name: str | None = None
    observation_time: datetime
    scores: dict[str, int]
    catatan: str | None
    total_score: int
    max_total: int
    percentage: float
    category: str | None
    pillars: list[PillarScore]
    alarms: list[AlarmItem]
    created_at: datetime


# ── Catalog (GET /observation/catalog) ──────────────────────────────────────────

class CatalogItem(BaseModel):
    item_code: str
    text: str


class CatalogPillar(BaseModel):
    key: str
    label: str
    items: list[CatalogItem]


class ObservationCatalog(BaseModel):
    pillars: list[CatalogPillar]
    total_items: int
    max_total: int
