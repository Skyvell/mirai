"""align unique constraint names with the metadata naming convention

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-09 15:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("biomarkers_slug_key", "biomarkers", type_="unique")
    op.create_unique_constraint("uq_biomarkers_slug", "biomarkers", ["slug"])
    op.drop_constraint("users_clerk_user_id_key", "users", type_="unique")
    op.create_unique_constraint("uq_users_clerk_user_id", "users", ["clerk_user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_clerk_user_id", "users", type_="unique")
    op.create_unique_constraint("users_clerk_user_id_key", "users", ["clerk_user_id"])
    op.drop_constraint("uq_biomarkers_slug", "biomarkers", type_="unique")
    op.create_unique_constraint("biomarkers_slug_key", "biomarkers", ["slug"])
