import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminOnly, AnyRole
from app.core.database import get_db
from app.schemas.incubator import (
    IncubatorCreate,
    IncubatorDetailResponse,
    IncubatorResponse,
    IncubatorUpdate,
)
from app.services import incubator_service

router = APIRouter()


@router.get("", response_model=list[IncubatorDetailResponse])
async def list_incubators(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    return await incubator_service.get_all_incubators(db)


@router.get("/available", response_model=list[IncubatorResponse])
async def list_available_incubators(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    """Returns only 'kosong' incubators — used when assigning a baby."""
    return await incubator_service.get_available_incubators(db)


@router.get("/{incubator_id}", response_model=IncubatorDetailResponse)
async def get_incubator(
    incubator_id: uuid.UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    return await incubator_service.get_incubator(incubator_id, db)


@router.post("", response_model=IncubatorResponse, status_code=status.HTTP_201_CREATED)
async def create_incubator(
    data: IncubatorCreate,
    request: Request,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await incubator_service.create_incubator(data, db, actor_id=current_user.id, ip=ip)


@router.put("/{incubator_id}", response_model=IncubatorResponse)
async def update_incubator(
    incubator_id: uuid.UUID,
    data: IncubatorUpdate,
    request: Request,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await incubator_service.update_incubator(
        incubator_id, data, db, actor_id=current_user.id, ip=ip
    )
