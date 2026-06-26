import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AnyRole, PerawatOrAdmin
from app.core.database import get_db
from app.schemas.monitoring import MonitoringCreate, MonitoringResponse, PhotoUploadResponse
from app.services import monitoring_service

router = APIRouter()


@router.post(
    "/babies/{baby_id}/monitoring",
    response_model=MonitoringResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_monitoring(
    baby_id: uuid.UUID,
    data: MonitoringCreate,
    request: Request,
    current_user: PerawatOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await monitoring_service.create_monitoring(
        baby_id, data, db, actor_id=current_user.id, ip=ip
    )


@router.get("/babies/{baby_id}/monitoring", response_model=list[MonitoringResponse])
async def list_monitoring(
    baby_id: uuid.UUID,
    current_user: AnyRole,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await monitoring_service.list_monitoring(baby_id, db, skip=skip, limit=limit)


@router.post(
    "/monitoring/{monitoring_id}/photo",
    response_model=PhotoUploadResponse,
)
async def upload_photo(
    monitoring_id: uuid.UUID,
    request: Request,
    current_user: PerawatOrAdmin,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await monitoring_service.upload_photo(
        monitoring_id, file, db, actor_id=current_user.id, ip=ip
    )
