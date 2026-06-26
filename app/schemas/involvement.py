import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


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


class InvolvementCreate(BaseModel):
    observation_time: datetime
    durasi_menyusui: int | None = None    # minutes (informational)
    durasi_interaksi: int | None = None   # minutes (informational)
    # Pillar 8 sub-domains, each 0–4
    presence_score: int | None = None
    physical_interaction_score: int | None = None
    feeding_participation_score: int | None = None
    care_participation_score: int | None = None
    knowledge_score: int | None = None
    communication_score: int | None = None
    emotional_readiness_score: int | None = None
    discharge_readiness_score: int | None = None
    catatan: str | None = None
    kondisi_bayi: str | None = None

    @field_validator("durasi_menyusui", "durasi_interaksi")
    @classmethod
    def non_negative(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Durasi tidak boleh negatif")
        return v

    @field_validator(*_DOMAIN_FIELDS)
    @classmethod
    def domain_range(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 4):
            raise ValueError("Skor domain harus antara 0 dan 4")
        return v


class InvolvementResponse(BaseModel):
    involvement_id: uuid.UUID
    baby_id: uuid.UUID
    recorded_by: uuid.UUID
    recorder_name: str | None = None
    observation_time: datetime
    durasi_menyusui: int | None
    durasi_interaksi: int | None
    presence_score: int | None
    physical_interaction_score: int | None
    feeding_participation_score: int | None
    care_participation_score: int | None
    knowledge_score: int | None
    communication_score: int | None
    emotional_readiness_score: int | None
    discharge_readiness_score: int | None
    catatan: str | None
    skor_keterlibatan: int | None        # Parent Engagement Index (PEI), 0–100
    skor_kategori: str | None = None     # Rendah / Sedang / Baik / Sangat Baik
    kondisi_bayi: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvolvementSummary(BaseModel):
    total_sessions: int
    avg_skor: float | None
    avg_durasi_menyusui: float | None
    avg_durasi_interaksi: float | None
    latest_skor: int | None
    latest_kategori: str | None
