from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AnyRole
from app.core.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard

router = APIRouter()


@router.get("", response_model=DashboardResponse)
async def dashboard(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard(db)
