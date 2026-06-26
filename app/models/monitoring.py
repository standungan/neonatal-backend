import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MonitoringRecord(Base):
    __tablename__ = "monitoring_records"

    monitoring_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    baby_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("babies.baby_id"), nullable=False
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    observation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    suhu_bayi: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))        # °C
    suhu_inkubator: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))   # °C
    kelembapan_inkubator: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))  # % RH (Pillar 7)
    heart_rate: Mapped[int | None] = mapped_column(SmallInteger)            # bpm
    respiratory_rate: Mapped[int | None] = mapped_column(SmallInteger)      # breaths/min (Pillar 1)
    spo2: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))             # %
    expression_score: Mapped[int | None] = mapped_column(SmallInteger)
    movement_score: Mapped[int | None] = mapped_column(SmallInteger)
    pain_score: Mapped[int | None] = mapped_column(SmallInteger)            # 0–7, Pillar 6
    sleep_duration_min: Mapped[int | None] = mapped_column(SmallInteger)    # minutes, Pillar 5
    sleep_quality: Mapped[int | None] = mapped_column(SmallInteger)         # 1–5, Pillar 5
    agitation_episodes: Mapped[int | None] = mapped_column(SmallInteger)    # count, Pillar 5
    catatan: Mapped[str | None] = mapped_column(Text)
    foto_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("expression_score BETWEEN 1 AND 5", name="ck_expression_score"),
        CheckConstraint("movement_score BETWEEN 1 AND 5", name="ck_movement_score"),
        CheckConstraint("pain_score BETWEEN 0 AND 7", name="ck_pain_score"),
        CheckConstraint("sleep_quality BETWEEN 1 AND 5", name="ck_sleep_quality"),
    )

    # relationships
    baby: Mapped["Baby"] = relationship(back_populates="monitoring_records")
    recorder: Mapped["User"] = relationship(back_populates="monitoring_records")
