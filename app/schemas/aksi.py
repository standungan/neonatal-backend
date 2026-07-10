import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class AksiCreate(BaseModel):
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


class ItemScore(BaseModel):
    item_code: str
    text: str
    score: int          # 0–3
    max: int            # 3
    percentage: float   # 0–100


class AlarmItem(BaseModel):
    item_code: str
    text: str
    score: int          # 0 or 1


class AksiResponse(BaseModel):
    aksi_id: uuid.UUID
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
    items: list[ItemScore]
    alarms: list[AlarmItem]
    created_at: datetime


class AksiSummary(BaseModel):
    total_sessions: int
    avg_percentage: float | None
    latest_percentage: float | None
    latest_category: str | None


# ── Catalog (GET /aksi/catalog) ─────────────────────────────────────────────────

class CatalogItem(BaseModel):
    item_code: str
    text: str


class AksiCatalog(BaseModel):
    key: str            # pillar key ("kolaborasi")
    label: str          # "Kolaborasi Interprofesional"
    items: list[CatalogItem]
    total_items: int
    max_total: int
