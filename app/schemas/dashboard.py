import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total: int
    terisi: int
    kosong: int
    warning: int
    tidak_tersedia: int


class BabySummary(BaseModel):
    baby_id: uuid.UUID
    baby_name: str
    age_in_days: int
    birth_weight: Decimal | None
    assigned_at: datetime


class LatestVitals(BaseModel):
    suhu_bayi: Decimal | None
    heart_rate: int | None
    spo2: Decimal | None
    observation_time: datetime
    vital_status: str   # "normal" | "warning"


class IncubatorDashboardItem(BaseModel):
    incubator_id: uuid.UUID
    incubator_no: str
    location: str | None
    status: str
    current_baby: BabySummary | None = None
    latest_vitals: LatestVitals | None = None


class DashboardResponse(BaseModel):
    stats: DashboardStats
    incubators: list[IncubatorDashboardItem]
