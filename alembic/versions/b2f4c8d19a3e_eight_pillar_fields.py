"""eight-pillar fields: monitoring vitals + parental involvement domains

Revision ID: b2f4c8d19a3e
Revises: a7821a4243e6
Create Date: 2026-06-22 00:00:00.000000

Adds Pillar 1/5/6 vitals to monitoring_records and the 8 Pillar-8 sub-domain
scores to parent_involvement_records. See docs/8 pillar NICU.md.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2f4c8d19a3e'
down_revision: Union[str, None] = 'a7821a4243e6'
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
    # monitoring_records — Pillar 1 (RR), Pillar 6 (pain), Pillar 5 (sleep/comfort)
    op.add_column("monitoring_records", sa.Column("respiratory_rate", sa.SmallInteger(), nullable=True))
    op.add_column("monitoring_records", sa.Column("pain_score", sa.SmallInteger(), nullable=True))
    op.add_column("monitoring_records", sa.Column("sleep_duration_min", sa.SmallInteger(), nullable=True))
    op.add_column("monitoring_records", sa.Column("sleep_quality", sa.SmallInteger(), nullable=True))
    op.add_column("monitoring_records", sa.Column("agitation_episodes", sa.SmallInteger(), nullable=True))
    op.create_check_constraint("ck_pain_score", "monitoring_records", "pain_score BETWEEN 0 AND 7")
    op.create_check_constraint("ck_sleep_quality", "monitoring_records", "sleep_quality BETWEEN 1 AND 5")

    # parent_involvement_records — Pillar 8 sub-domains (0–4 each)
    for col in _DOMAIN_COLS:
        op.add_column("parent_involvement_records", sa.Column(col, sa.SmallInteger(), nullable=True))
        op.create_check_constraint(f"ck_{col}", "parent_involvement_records", f"{col} BETWEEN 0 AND 4")


def downgrade() -> None:
    for col in _DOMAIN_COLS:
        op.drop_constraint(f"ck_{col}", "parent_involvement_records", type_="check")
        op.drop_column("parent_involvement_records", col)

    op.drop_constraint("ck_sleep_quality", "monitoring_records", type_="check")
    op.drop_constraint("ck_pain_score", "monitoring_records", type_="check")
    for col in ("agitation_episodes", "sleep_quality", "sleep_duration_min", "pain_score", "respiratory_rate"):
        op.drop_column("monitoring_records", col)
