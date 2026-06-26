import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


async def save_photo(file: UploadFile, baby_id: uuid.UUID, monitoring_id: uuid.UUID) -> str:
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Format file harus JPEG, PNG, atau WebP",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ukuran file maksimal 5 MB",
        )

    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    relative_path = f"{baby_id}/{monitoring_id}{ext}"

    if settings.storage_backend == "local":
        return await _save_local(contents, relative_path)

    # S3 path (to be wired when STORAGE_BACKEND=s3)
    raise HTTPException(status_code=500, detail="S3 storage not configured")


async def _save_local(contents: bytes, relative_path: str) -> str:
    dest = Path(settings.storage_local_path) / relative_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(contents)
    return f"/uploads/{relative_path}"
