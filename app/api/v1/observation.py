import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AnyRole, PerawatOrAdmin
from app.core.database import get_db
from app.schemas.observation import ObservationCatalog, ObservationCreate, ObservationResponse
from app.services import observation_service

router = APIRouter()


@router.get("/observation/catalog", response_model=ObservationCatalog)
async def observation_catalog(current_user: AnyRole):
    """The fixed 8-pillar / 54-item catalog (source of truth for the form)."""
    return observation_service.get_catalog()


@router.post(
    "/babies/{baby_id}/observation",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_observation(
    baby_id: uuid.UUID,
    data: ObservationCreate,
    request: Request,
    current_user: PerawatOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await observation_service.create_observation(
        baby_id, data, db, actor_id=current_user.id, ip=ip
    )


@router.get("/babies/{baby_id}/observation", response_model=list[ObservationResponse])
async def list_observations(
    baby_id: uuid.UUID,
    current_user: AnyRole,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await observation_service.list_observations(baby_id, db, skip=skip, limit=limit)
