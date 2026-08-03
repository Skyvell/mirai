"""rename draft table to lab_results, revise upload status, add updated_at

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-02 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename the draft table and realign its constraints/index to the convention.
    op.rename_table("draft_biomarker_measurements", "lab_results")
    op.execute(
        "ALTER TABLE lab_results RENAME CONSTRAINT "
        "pk_draft_biomarker_measurements TO pk_lab_results"
    )
    op.execute(
        "ALTER TABLE lab_results RENAME CONSTRAINT "
        "fk_draft_biomarker_measurements_biomarkers_biomarker_id "
        "TO fk_lab_results_biomarkers_biomarker_id"
    )
    op.execute(
        "ALTER TABLE lab_results RENAME CONSTRAINT "
        "fk_draft_biomarker_measurements_lab_uploads_lab_upload_id "
        "TO fk_lab_results_lab_uploads_lab_upload_id"
    )
    op.execute(
        "ALTER INDEX ix_draft_biomarker_measurements_lab_upload_id "
        "RENAME TO ix_lab_results_lab_upload_id"
    )

    # Drop the unused skip_reason column; biomarker_id IS NULL already marks unmatched rows.
    op.drop_column("lab_results", "skip_reason")

    # Rename the upload's confirm timestamp to match the confirmed status.
    op.alter_column("lab_uploads", "committed_at", new_column_name="confirmed_at")

    # Track last-modification on the PATCH-able tables.
    for table in ("biomarker_measurements", "lab_results"):
        op.add_column(
            table,
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    # Rebrand the stored status values (non-native enum, so plain data updates).
    op.execute("UPDATE lab_uploads SET status = 'confirmed' WHERE status = 'committed'")
    op.execute("UPDATE lab_uploads SET status = 'queued' WHERE status = 'pending'")


def downgrade() -> None:
    op.execute("UPDATE lab_uploads SET status = 'pending' WHERE status = 'queued'")
    op.execute("UPDATE lab_uploads SET status = 'committed' WHERE status = 'confirmed'")

    op.drop_column("lab_results", "updated_at")
    op.drop_column("biomarker_measurements", "updated_at")

    op.alter_column("lab_uploads", "confirmed_at", new_column_name="committed_at")

    op.add_column("lab_results", sa.Column("skip_reason", sa.Text(), nullable=True))

    op.execute(
        "ALTER INDEX ix_lab_results_lab_upload_id "
        "RENAME TO ix_draft_biomarker_measurements_lab_upload_id"
    )
    op.execute(
        "ALTER TABLE lab_results RENAME CONSTRAINT "
        "fk_lab_results_lab_uploads_lab_upload_id "
        "TO fk_draft_biomarker_measurements_lab_uploads_lab_upload_id"
    )
    op.execute(
        "ALTER TABLE lab_results RENAME CONSTRAINT "
        "fk_lab_results_biomarkers_biomarker_id "
        "TO fk_draft_biomarker_measurements_biomarkers_biomarker_id"
    )
    op.execute(
        "ALTER TABLE lab_results RENAME CONSTRAINT "
        "pk_lab_results TO pk_draft_biomarker_measurements"
    )
    op.rename_table("lab_results", "draft_biomarker_measurements")
