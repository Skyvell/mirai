"""make biomarker_measurements.lab_upload_id nullable

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-12 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "biomarker_measurements",
        "lab_upload_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )


def downgrade() -> None:
    # Lossy once manual or orphaned rows exist; they must be removed first.
    op.alter_column(
        "biomarker_measurements",
        "lab_upload_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
