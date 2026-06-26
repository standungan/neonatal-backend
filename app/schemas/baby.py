import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


GenderType = Literal["laki_laki", "perempuan"]


# ---------- sub-schemas ----------

class ParentCreate(BaseModel):
    mother_name: str | None = None
    father_name: str | None = None
    mother_phone: str | None = None
    mother_medical_history: str | None = None
    birth_history: str | None = None
    delivery_history: str | None = None
    additional_notes: str | None = None


class ParentResponse(BaseModel):
    parent_id: uuid.UUID
    mother_name: str | None
    father_name: str | None
    mother_phone: str | None
    mother_medical_history: str | None
    birth_history: str | None
    delivery_history: str | None
    additional_notes: str | None

    model_config = {"from_attributes": True}


class AssignmentInfo(BaseModel):
    assignment_id: uuid.UUID
    incubator_id: uuid.UUID
    incubator_no: str
    location: str | None
    assigned_at: datetime
    assigned_by_name: str | None = None


# ---------- baby request ----------

class BabyCreate(BaseModel):
    # baby
    baby_name: str
    gender: GenderType
    birth_date: date
    birth_weight: Decimal | None = None    # grams
    birth_length: Decimal | None = None    # cm
    gestational_age: int | None = None     # weeks
    birth_type: str | None = None
    clinical_notes: str | None = None
    # parent (created together)
    parent: ParentCreate
    # assignment
    incubator_id: uuid.UUID


class BabyUpdate(BaseModel):
    baby_name: str | None = None
    clinical_notes: str | None = None
    birth_weight: Decimal | None = None


# ---------- baby response ----------

class BabyResponse(BaseModel):
    baby_id: uuid.UUID
    baby_name: str
    gender: str
    birth_date: date
    birth_weight: Decimal | None
    birth_length: Decimal | None
    gestational_age: int | None
    birth_type: str | None
    clinical_notes: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BabyDetailResponse(BabyResponse):
    age_in_days: int
    parent: ParentResponse | None = None
    current_assignment: AssignmentInfo | None = None
    latest_vitals: "MonitoringSummary | None" = None


class MonitoringSummary(BaseModel):
    monitoring_id: uuid.UUID
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
