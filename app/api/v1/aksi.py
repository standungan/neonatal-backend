import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AnyRole, PerawatOrAdmin
from app.core.database import get_db
from app.schemas.aksi import AksiCatalog, AksiCreate, AksiResponse, AksiSummary
from app.services import aksi_service

router = APIRouter()


@router.get("/aksi/catalog", response_model=AksiCatalog)
async def aksi_catalog(current_user: AnyRole):
    """Pillar 8 "Kolaborasi Interprofesional" — 6 items, source of truth for the form."""
    return aksi_service.get_catalog()


@router.post(
    "/babies/{baby_id}/aksi",
    response_model=AksiResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_aksi(
    baby_id: uuid.UUID,
    data: AksiCreate,
    request: Request,
    current_user: PerawatOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await aksi_service.create_aksi(baby_id, data, db, actor_id=current_user.id, ip=ip)


@router.get("/babies/{baby_id}/aksi", response_model=list[AksiResponse])
async def list_aksi(
    baby_id: uuid.UUID,
    current_user: AnyRole,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await aksi_service.list_aksi(baby_id, db, skip=skip, limit=limit)


@router.get("/babies/{baby_id}/aksi/summary", response_model=AksiSummary)
async def aksi_summary(
    baby_id: uuid.UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    return await aksi_service.get_aksi_summary(baby_id, db)
