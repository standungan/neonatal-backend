import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Baby(Base):
    __tablename__ = "babies"

    baby_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    baby_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(
        Enum("laki_laki", "perempuan", name="gender_type"), nullable=False
    )
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))      # grams
    birth_length: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))      # cm
    gestational_age: Mapped[int | None] = mapped_column(SmallInteger)        # weeks
    birth_type: Mapped[str | None] = mapped_column(String(100))
    clinical_notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    parent: Mapped["Parent"] = relationship(back_populates="baby", uselist=False)
    assignments: Mapped[list["BabyIncubatorAssignment"]] = relationship(back_populates="baby")
    monitoring_records: Mapped[list["MonitoringRecord"]] = relationship(
        back_populates="baby", order_by="MonitoringRecord.observation_time.desc()"
    )
    involvement_records: Mapped[list["ParentInvolvementRecord"]] = relationship(
        back_populates="baby", order_by="ParentInvolvementRecord.observation_time.desc()"
    )
