"""observations table (8-pillar observation instrument)

Revision ID: d4b8f1e6c920
Revises: c3a5e7f20b1d
Create Date: 2026-07-07 00:00:00.000000

Adds the observations table for the 54-item / 8-pillar premature-baby
observation instrument (see updates01/Kuis Observasi Bayi.pdf).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd4b8f1e6c920'
down_revision: Union[str, None] = 'c3a5e7f20b1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("observation_id", postgresql.UUID(as_uuid=True), primary_key=True,
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
    op.create_index("idx_observation_baby_time", "observations",
                    ["baby_id", sa.text("observation_time DESC")])


def downgrade() -> None:
    op.drop_index("idx_observation_baby_time", table_name="observations")
    op.drop_table("observations")
