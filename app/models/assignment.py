import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BabyIncubatorAssignment(Base):
    __tablename__ = "baby_incubator_assignments"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    baby_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("babies.baby_id"), nullable=False
    )
    incubator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incubators.incubator_id"), nullable=False
    )
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    discharged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        Enum("active", "discharged", name="assignment_status"),
        nullable=False,
        default="active",
    )
    # ── registration / admission data (updates02) ──────────────────────────────
    # assigned_at = tanggal masuk NICU · assigned_by = perawat penerima ·
    # incubator_id = nomor inkubator. These add the rest of "Data Registrasi".
    no_registrasi_nicu: Mapped[str | None] = mapped_column(String(30), unique=True)
    rumah_sakit: Mapped[str | None] = mapped_column(String(150))
    ruang_nicu: Mapped[str | None] = mapped_column(String(100))
    dpjp_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    # relationships
    baby: Mapped["Baby"] = relationship(back_populates="assignments")
    incubator: Mapped["Incubator"] = relationship(back_populates="assignments")
    assigned_by_user: Mapped["User"] = relationship(
        back_populates="assignments", foreign_keys=[assigned_by]
    )
    dpjp: Mapped["User"] = relationship(foreign_keys=[dpjp_id])
