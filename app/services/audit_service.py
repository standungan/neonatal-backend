import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    action: str,
    table_name: str | None = None,
    record_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    details: dict | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        ip_address=ip_address,
        details=details,
    )
    db.add(entry)
    # flush is handled by the session commit in get_db
