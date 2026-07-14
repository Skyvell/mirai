"""create draft_biomarker_measurements

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-14 10:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "draft_biomarker_measurements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lab_upload_id", sa.Uuid(), nullable=False),
        sa.Column("biomarker_id", sa.Uuid(), nullable=True),
        sa.Column("value", sa.Numeric(12, 4), nullable=True),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("reference_low", sa.Numeric(12, 4), nullable=True),
        sa.Column("reference_high", sa.Numeric(12, 4), nullable=True),
        sa.Column("source_name", sa.Text(), nullable=True),
        sa.Column("skip_reason", sa.Text(), nullable=True),
        sa.Column("included", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_draft_biomarker_measurements"),
        sa.ForeignKeyConstraint(
            ["lab_upload_id"],
            ["lab_uploads.id"],
            name="fk_draft_biomarker_measurements_lab_uploads_lab_upload_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["biomarker_id"],
            ["biomarkers.id"],
            name="fk_draft_biomarker_measurements_biomarkers_biomarker_id",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_draft_biomarker_measurements_lab_upload_id",
        "draft_biomarker_measurements",
        ["lab_upload_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_draft_biomarker_measurements_lab_upload_id", table_name="draft_biomarker_measurements"
    )
    op.drop_table("draft_biomarker_measurements")
