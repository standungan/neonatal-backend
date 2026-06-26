from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminOnly
from app.core.database import get_db
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditLogResponse

router = APIRouter()


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    current_user: AdminOnly,
    skip: int = 0,
    limit: int = 100,
    action: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    logs = await AuditRepository(db).get_all(skip=skip, limit=limit, action=action)
    return [
        AuditLogResponse(
            log_id=log.log_id,
            user_id=log.user_id,
            user_name=log.user.full_name if log.user else None,
            action=log.action,
            table_name=log.table_name,
            record_id=log.record_id,
            ip_address=str(log.ip_address) if log.ip_address else None,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]
