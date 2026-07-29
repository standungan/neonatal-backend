import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    PasswordResetRequest,
    UserCreate,
    UserOption,
    UserResponse,
    UserUpdate,
)
from app.services.audit_service import log_action


async def get_all_users(db: AsyncSession) -> list[UserResponse]:
    repo = UserRepository(db)
    users = await repo.get_all()
    return [UserResponse.model_validate(u) for u in users]


async def get_doctors(db: AsyncSession) -> list[UserOption]:
    """Active doctors — for the DPJP dropdown on baby registration."""
    doctors = await UserRepository(db).get_by_role("dokter", active_only=True)
    return [UserOption.model_validate(u) for u in doctors]


async def get_user(user_id: uuid.UUID, db: AsyncSession) -> UserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")
    return UserResponse.model_validate(user)


async def create_user(
    data: UserCreate,
    db: AsyncSession,
    actor_id: uuid.UUID | None = None,
    ip: str | None = None,
) -> UserResponse:
    repo = UserRepository(db)

    if await repo.email_exists(data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email sudah digunakan")

    user = User(
        role=data.role,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    user = await repo.create(user)

    await log_action(
        db,
        user_id=actor_id,
        action="CREATE",
        table_name="users",
        record_id=user.id,
        ip_address=ip,
        details={"email": user.email, "role": user.role},
    )
    return UserResponse.model_validate(user)


async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: AsyncSession,
    actor_id: uuid.UUID | None = None,
    ip: str | None = None,
) -> UserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.is_active is not None:
        user.is_active = data.is_active

    user = await repo.update(user)

    await log_action(
        db,
        user_id=actor_id,
        action="UPDATE",
        table_name="users",
        record_id=user_id,
        ip_address=ip,
    )
    return UserResponse.model_validate(user)


async def reset_password(
    user_id: uuid.UUID,
    data: PasswordResetRequest,
    db: AsyncSession,
    actor_id: uuid.UUID | None = None,
    ip: str | None = None,
) -> None:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    user.password_hash = hash_password(data.new_password)
    await repo.update(user)

    await log_action(
        db,
        user_id=actor_id,
        action="RESET_PASSWORD",
        table_name="users",
        record_id=user_id,
        ip_address=ip,
    )


async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession,
    actor_id: uuid.UUID | None = None,
    ip: str | None = None,
) -> None:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    if str(user_id) == str(actor_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak dapat menonaktifkan akun sendiri",
        )

    user.is_active = False
    await repo.update(user)

    await log_action(
        db,
        user_id=actor_id,
        action="DEACTIVATE",
        table_name="users",
        record_id=user_id,
        ip_address=ip,
    )
