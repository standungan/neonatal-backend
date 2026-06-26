import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class MonitoringCreate(BaseModel):
    observation_time: datetime
    suhu_bayi: Decimal | None = None
    suhu_inkubator: Decimal | None = None
    kelembapan_inkubator: Decimal | None = None
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    spo2: Decimal | None = None
    expression_score: int | None = None
    movement_score: int | None = None
    pain_score: int | None = None
    sleep_duration_min: int | None = None
    sleep_quality: int | None = None
    agitation_episodes: int | None = None
    catatan: str | None = None

    @field_validator("expression_score", "movement_score", "sleep_quality")
    @classmethod
    def score_range(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("Score harus antara 1 dan 5")
        return v

    @field_validator("pain_score")
    @classmethod
    def pain_range(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 7):
            raise ValueError("Pain score harus antara 0 dan 7")
        return v


class MonitoringResponse(BaseModel):
    monitoring_id: uuid.UUID
    baby_id: uuid.UUID
    recorded_by: uuid.UUID
    recorder_name: str | None = None
    observation_time: datetime
    suhu_bayi: Decimal | None
    suhu_inkubator: Decimal | None
    kelembapan_inkubator: Decimal | None
    heart_rate: int | None
    respiratory_rate: int | None
    spo2: Decimal | None
    expression_score: int | None
    movement_score: int | None
    pain_score: int | None
    sleep_duration_min: int | None
    sleep_quality: int | None
    agitation_episodes: int | None
    catatan: str | None
    foto_url: str | None
    vital_status: str = "normal"  # "normal" | "warning"
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoUploadResponse(BaseModel):
    monitoring_id: uuid.UUID
    foto_url: str
