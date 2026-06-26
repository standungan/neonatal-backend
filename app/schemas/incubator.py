import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


IncubatorStatus = Literal["kosong", "terisi", "warning", "tidak_tersedia"]


class IncubatorCreate(BaseModel):
    incubator_no: str
    location: str | None = None


class IncubatorUpdate(BaseModel):
    location: str | None = None
    status: IncubatorStatus | None = None


class CurrentBabySummary(BaseModel):
    baby_id: uuid.UUID
    baby_name: str
    birth_date: datetime | None = None
    assigned_at: datetime


class IncubatorResponse(BaseModel):
    incubator_id: uuid.UUID
    incubator_no: str
    location: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncubatorDetailResponse(IncubatorResponse):
    current_baby: CurrentBabySummary | None = None
