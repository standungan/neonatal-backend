"""rework parent_involvement_records to Pillar 6 (Kerjasama dengan Keluarga)

Revision ID: e5c9a2f7d418
Revises: d4b8f1e6c920
Create Date: 2026-07-08 00:00:00.000000

Replaces the FICare 8-domain (0–4) Parent Engagement Index model with Pillar 6
of the observation instrument: 6 items scored 0–3, stored as JSONB, with a
computed total_score / percentage / category (see updates01/Kuis Observasi Bayi.pdf).
Contextual columns (durasi_menyusui, durasi_interaksi, kondisi_bayi, catatan) are kept.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'e5c9a2f7d418'
down_revision: Union[str, None] = 'd4b8f1e6c920'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DOMAIN_COLS = (
    "presence_score",
    "physical_interaction_score",
    "feeding_participation_score",
    "care_participation_score",
    "knowledge_score",
    "communication_score",
    "emotional_readiness_score",
    "discharge_readiness_score",
)


def upgrade() -> None:
    # new Pillar-6 columns
    op.add_column("parent_involvement_records",
                  sa.Column("scores", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("parent_involvement_records",
                  sa.Column("total_score", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("parent_involvement_records",
                  sa.Column("percentage", sa.Numeric(5, 2), nullable=False, server_default="0"))
    op.add_column("parent_involvement_records",
                  sa.Column("category", sa.String(30)))

    # Drop the FICare 8-domain model. Dropping each column also drops its
    # single-column CHECK constraint automatically, regardless of the constraint's
    # name (inline auto-named when built from schema.sql, or ck_* from the model).
    for col in _DOMAIN_COLS:
        op.drop_column("parent_involvement_records", col)
    op.drop_column("parent_involvement_records", "skor_keterlibatan")


def downgrade() -> None:
    op.add_column("parent_involvement_records",
                  sa.Column("skor_keterlibatan", sa.SmallInteger()))
    op.create_check_constraint("ck_skor_keterlibatan", "parent_involvement_records",
                               "skor_keterlibatan BETWEEN 0 AND 100")
    for col in _DOMAIN_COLS:
        op.add_column("parent_involvement_records", sa.Column(col, sa.SmallInteger()))
        op.create_check_constraint(f"ck_{col}", "parent_involvement_records", f"{col} BETWEEN 0 AND 4")

    op.drop_column("parent_involvement_records", "category")
    op.drop_column("parent_involvement_records", "percentage")
    op.drop_column("parent_involvement_records", "total_score")
    op.drop_column("parent_involvement_records", "scores")
