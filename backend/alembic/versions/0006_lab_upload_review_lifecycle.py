"""lab upload review lifecycle: new status values, columns, and backfill

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-14 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_VALUES = "'uploaded', 'parsed', 'failed'"
_NEW_VALUES = "'pending', 'processing', 'awaiting_review', 'committed', 'failed'"


def upgrade() -> None:
    # New lifecycle columns.
    op.add_column("lab_uploads", sa.Column("measured_at", sa.Date(), nullable=True))
    op.add_column("lab_uploads", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column(
        "lab_uploads",
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Drop the old status CHECK and widen the column to fit the longer values.
    op.execute("ALTER TABLE lab_uploads DROP CONSTRAINT IF EXISTS lab_upload_status")
    op.execute("ALTER TABLE lab_uploads DROP CONSTRAINT IF EXISTS ck_lab_uploads_lab_upload_status")
    op.alter_column(
        "lab_uploads",
        "status",
        type_=sa.String(length=15),
        existing_type=sa.String(length=8),
        existing_nullable=False,
    )

    # Remap existing rows: parsed data is already in the series (committed);
    # anything still 'uploaded' never parsed and is treated as failed.
    op.execute(
        "UPDATE lab_uploads SET status = 'committed', committed_at = parsed_at "
        "WHERE status = 'parsed'"
    )
    op.execute("UPDATE lab_uploads SET status = 'failed' WHERE status = 'uploaded'")

    op.create_check_constraint(
        "ck_lab_uploads_lab_upload_status",
        "lab_uploads",
        f"status IN ({_NEW_VALUES})",
    )


def downgrade() -> None:
    op.execute("ALTER TABLE lab_uploads DROP CONSTRAINT IF EXISTS ck_lab_uploads_lab_upload_status")

    # Collapse the richer lifecycle back onto the old three values (lossy).
    op.execute(
        "UPDATE lab_uploads SET status = 'parsed' "
        "WHERE status IN ('pending', 'processing', 'awaiting_review', 'committed')"
    )

    op.alter_column(
        "lab_uploads",
        "status",
        type_=sa.String(length=8),
        existing_type=sa.String(length=15),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "lab_upload_status",
        "lab_uploads",
        f"status IN ({_OLD_VALUES})",
    )

    op.drop_column("lab_uploads", "committed_at")
    op.drop_column("lab_uploads", "error_message")
    op.drop_column("lab_uploads", "measured_at")
