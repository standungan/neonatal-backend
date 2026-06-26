from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.audit_service import log_action


async def login(data: LoginRequest, db: AsyncSession, ip: str | None = None) -> TokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_email(data.email)

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun tidak aktif",
        )

    await log_action(
        db,
        user_id=user.id,
        action="LOGIN",
        ip_address=ip,
        details={"email": user.email},
    )

    token = create_access_token(str(user.id), user.role)
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        full_name=user.full_name,
        role=user.role,
    )
