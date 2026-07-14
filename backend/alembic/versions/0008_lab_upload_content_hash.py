"""lab_upload content hash

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-14 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lab_uploads",
        sa.Column("content_sha256", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_lab_uploads_content_sha256",
        "lab_uploads",
        ["content_sha256"],
    )


def downgrade() -> None:
    op.drop_index("ix_lab_uploads_content_sha256", table_name="lab_uploads")
    op.drop_column("lab_uploads", "content_sha256")
