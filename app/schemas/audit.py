import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    log_id: uuid.UUID
    user_id: uuid.UUID | None
    user_name: str | None
    action: str
    table_name: str | None
    record_id: uuid.UUID | None
    ip_address: str | None
    details: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
