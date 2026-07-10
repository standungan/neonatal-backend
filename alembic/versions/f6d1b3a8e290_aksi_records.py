"""aksi_records table (Menu Aksi — Kolaborasi Interprofesional)

Revision ID: f6d1b3a8e290
Revises: e5c9a2f7d418
Create Date: 2026-07-10 00:00:00.000000

Adds the aksi_records table for the Menu Aksi module — Pillar 8 "Kolaborasi
Interprofesional" pulled out of the Monitoring Bayi (8-pillar observation)
instrument: 6 items scored 0–3 (see updates01/Kuis Observasi Bayi.pdf).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f6d1b3a8e290'
down_revision: Union[str, None] = 'e5c9a2f7d418'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "aksi_records",
        sa.Column("aksi_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("baby_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("babies.baby_id"), nullable=False),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("observation_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scores", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("catatan", sa.Text()),
        sa.Column("total_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("category", sa.String(30)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_aksi_baby_time", "aksi_records",
                    ["baby_id", sa.text("observation_time DESC")])


def downgrade() -> None:
    op.drop_index("idx_aksi_baby_time", table_name="aksi_records")
    op.drop_table("aksi_records")
