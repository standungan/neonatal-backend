from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import (
    aksi,
    audit,
    auth,
    babies,
    dashboard,
    incubators,
    involvement,
    monitoring,
    observation,
    reports,
    users,
)
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = Path(settings.storage_local_path)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

app.include_router(auth.router,        prefix="/api/v1/auth",        tags=["Auth"])
app.include_router(users.router,       prefix="/api/v1/users",       tags=["Users"])
app.include_router(incubators.router,  prefix="/api/v1/incubators",  tags=["Incubators"])
app.include_router(babies.router,      prefix="/api/v1/babies",      tags=["Babies"])
app.include_router(monitoring.router,  prefix="/api/v1",             tags=["Monitoring"])
app.include_router(involvement.router, prefix="/api/v1",             tags=["Involvement"])
app.include_router(observation.router, prefix="/api/v1",             tags=["Observation"])
app.include_router(aksi.router,        prefix="/api/v1",             tags=["Aksi"])
app.include_router(dashboard.router,   prefix="/api/v1/dashboard",   tags=["Dashboard"])
app.include_router(reports.router,     prefix="/api/v1",             tags=["Reports"])
app.include_router(audit.router,       prefix="/api/v1/audit-logs",  tags=["Audit"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.app_version}
