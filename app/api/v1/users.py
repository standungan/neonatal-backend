import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminOnly
from app.core.database import get_db
from app.schemas.user import PasswordResetRequest, UserCreate, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    return await user_service.get_all_users(db)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    request: Request,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await user_service.create_user(data, db, actor_id=current_user.id, ip=ip)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    return await user_service.get_user(user_id, db)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    request: Request,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await user_service.update_user(user_id, data, db, actor_id=current_user.id, ip=ip)


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: uuid.UUID,
    data: PasswordResetRequest,
    request: Request,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    await user_service.reset_password(user_id, data, db, actor_id=current_user.id, ip=ip)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    current_user: AdminOnly,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    await user_service.deactivate_user(user_id, db, actor_id=current_user.id, ip=ip)
