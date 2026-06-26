from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import login

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login_route(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return await login(data, db, ip=ip)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return UserResponse.model_validate(current_user)
