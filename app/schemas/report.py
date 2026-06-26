import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.baby import BabyDetailResponse
from app.schemas.involvement import InvolvementResponse, InvolvementSummary
from app.schemas.monitoring import MonitoringResponse


class BabyReportResponse(BaseModel):
    baby: BabyDetailResponse
    monitoring_history: list[MonitoringResponse]
    involvement_history: list[InvolvementResponse]
    involvement_summary: InvolvementSummary
    generated_at: datetime
