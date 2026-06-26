"""monitoring: add incubator humidity (Pillar 7)

Revision ID: c3a5e7f20b1d
Revises: b2f4c8d19a3e
Create Date: 2026-06-25 00:00:00.000000

Adds kelembapan_inkubator (% RH) to monitoring_records.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3a5e7f20b1d'
down_revision: Union[str, None] = 'b2f4c8d19a3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "monitoring_records",
        sa.Column("kelembapan_inkubator", sa.Numeric(5, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("monitoring_records", "kelembapan_inkubator")
