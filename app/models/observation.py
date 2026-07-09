import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Observation(Base):
    """One 8-pillar observation session (54 items scored 0–3, stored as JSONB)."""

    __tablename__ = "observations"

    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    baby_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("babies.baby_id"), nullable=False
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    observation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # { item_code: score(0-3) }
    scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    catatan: Mapped[str | None] = mapped_column(Text)
    # computed at write time (also recomputed on read from the catalog)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    category: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # one-directional relationship (no back_populates → no change to User model)
    recorder: Mapped["User"] = relationship("User")  # noqa: F821
