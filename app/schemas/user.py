import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


UserRole = Literal["admin", "perawat", "dokter"]


class UserCreate(BaseModel):
    role: UserRole
    email: EmailStr
    password: str
    full_name: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    is_active: bool | None = None


class PasswordResetRequest(BaseModel):
    new_password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    role: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
