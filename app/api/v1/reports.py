import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AnyRole
from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.report import BabyReportResponse
from app.services.pdf_service import generate_pdf
from app.services.report_service import get_baby_report

router = APIRouter()

_optional_bearer = HTTPBearer(auto_error=False)


@router.get("/babies/{baby_id}/report", response_model=BabyReportResponse)
async def baby_report(
    baby_id: uuid.UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    return await get_baby_report(baby_id, db)


@router.get("/babies/{baby_id}/report/pdf")
async def baby_report_pdf(
    baby_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: str | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
):
    """
    Accepts auth via Bearer header (API calls) or ?token= query param
    (browser download via url_launcher which cannot set headers).
    """
    raw_token: str | None = None
    if credentials:
        raw_token = credentials.credentials
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated")

    payload = decode_access_token(raw_token)
    user_id = payload.get("sub") if payload else None
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token tidak valid")

    user = await UserRepository(db).get_by_id(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User tidak aktif")

    report = await get_baby_report(baby_id, db)
    pdf_bytes = generate_pdf(report)
    filename = f"laporan_{report.baby.baby_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
