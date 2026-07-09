import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class InvolvementCreate(BaseModel):
    observation_time: datetime
    scores: dict[str, int]                 # { item_code: 0-3 }
    catatan: str | None = None
    durasi_menyusui: int | None = None     # minutes (informational)
    durasi_interaksi: int | None = None    # minutes (informational)
    kondisi_bayi: str | None = None

    @field_validator("scores")
    @classmethod
    def scores_in_range(cls, v: dict[str, int]) -> dict[str, int]:
        for code, score in v.items():
            if not isinstance(score, int) or not (0 <= score <= 3):
                raise ValueError(f"Skor '{code}' harus bilangan 0–3")
        return v

    @field_validator("durasi_menyusui", "durasi_interaksi")
    @classmethod
    def non_negative(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Durasi tidak boleh negatif")
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


class InvolvementResponse(BaseModel):
    involvement_id: uuid.UUID
    baby_id: uuid.UUID
    recorded_by: uuid.UUID
    recorder_name: str | None = None
    observation_time: datetime
    scores: dict[str, int]
    catatan: str | None
    durasi_menyusui: int | None
    durasi_interaksi: int | None
    kondisi_bayi: str | None
    total_score: int
    max_total: int
    percentage: float
    category: str | None
    items: list[ItemScore]
    alarms: list[AlarmItem]
    created_at: datetime


class InvolvementSummary(BaseModel):
    total_sessions: int
    avg_percentage: float | None
    latest_percentage: float | None
    latest_category: str | None
    avg_durasi_menyusui: float | None
    avg_durasi_interaksi: float | None


# ── Catalog (GET /involvement/catalog) ──────────────────────────────────────────

class CatalogItem(BaseModel):
    item_code: str
    text: str


class InvolvementCatalog(BaseModel):
    key: str            # pillar key ("keluarga")
    label: str          # "Kerjasama dengan Keluarga"
    items: list[CatalogItem]
    total_items: int
    max_total: int
