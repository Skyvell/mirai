"""require measured_at on biomarker_measurements

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-16 22:54:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "biomarker_measurements",
        "measured_at",
        existing_type=sa.Date(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "biomarker_measurements",
        "measured_at",
        existing_type=sa.Date(),
        nullable=True,
    )
