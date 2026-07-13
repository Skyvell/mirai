"""default lab_upload_id FK to SET NULL and align its name with the convention

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-13 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "biomarker_measurements_lab_upload_id_fkey",
        "biomarker_measurements",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_biomarker_measurements_lab_uploads_lab_upload_id",
        "biomarker_measurements",
        "lab_uploads",
        ["lab_upload_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_biomarker_measurements_lab_uploads_lab_upload_id",
        "biomarker_measurements",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "biomarker_measurements_lab_upload_id_fkey",
        "biomarker_measurements",
        "lab_uploads",
        ["lab_upload_id"],
        ["id"],
        ondelete="CASCADE",
    )
