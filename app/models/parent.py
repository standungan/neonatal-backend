import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Parent(Base):
    __tablename__ = "parents"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    baby_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("babies.baby_id", ondelete="CASCADE"), unique=True, nullable=False
    )
    mother_name: Mapped[str | None] = mapped_column(String(255))
    father_name: Mapped[str | None] = mapped_column(String(255))
    mother_phone: Mapped[str | None] = mapped_column(String(20))
    mother_medical_history: Mapped[str | None] = mapped_column(Text)
    birth_history: Mapped[str | None] = mapped_column(Text)
    delivery_history: Mapped[str | None] = mapped_column(Text)
    additional_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationship
    baby: Mapped["Baby"] = relationship(back_populates="parent")
