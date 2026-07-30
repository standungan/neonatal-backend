import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.aksi import AksiResponse
from app.schemas.baby import BabyDetailResponse
from app.schemas.involvement import InvolvementResponse, InvolvementSummary
from app.schemas.monitoring import MonitoringResponse
from app.schemas.observation import ObservationResponse


class BabyReportResponse(BaseModel):
    baby: BabyDetailResponse
    monitoring_history: list[MonitoringResponse]
    involvement_history: list[InvolvementResponse]
    involvement_summary: InvolvementSummary
    # latest 8-pillar assessments (updates: shown in the PDF's "Penilaian 8 Pilar")
    observation_latest: ObservationResponse | None = None
    aksi_latest: AksiResponse | None = None
    generated_at: datetime
