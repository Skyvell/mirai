"""explicit interval strata

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14 00:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STRATUM_COLUMNS = ["biomarker_id", "type", "sex", "age_min_days"]

intervals = sa.table(
    "biomarker_intervals",
    sa.column("id", sa.Uuid()),
    sa.column("biomarker_id", sa.Uuid()),
    sa.column("type", sa.Text()),
    sa.column("sex", sa.Text()),
    sa.column("age_min_days", sa.Integer()),
    sa.column("age_max_days", sa.Integer()),
    sa.column("interval_low", sa.Numeric(precision=12, scale=4)),
    sa.column("interval_high", sa.Numeric(precision=12, scale=4)),
    sa.column("source", sa.Text()),
    sa.column("source_url", sa.Text()),
)


def upgrade() -> None:
    connection = op.get_bind()
    unisex = connection.execute(
        sa.select(
            intervals.c.biomarker_id,
            intervals.c.type,
            intervals.c.age_min_days,
            intervals.c.age_max_days,
            intervals.c.interval_low,
            intervals.c.interval_high,
            intervals.c.source,
            intervals.c.source_url,
        ).where(intervals.c.sex.is_(None))
    ).mappings()

    female_copies = [{**row, "id": uuid.uuid7(), "sex": "female"} for row in unisex]
    if female_copies:
        op.bulk_insert(intervals, female_copies)
    op.execute(intervals.update().where(intervals.c.sex.is_(None)).values(sex="male"))
    op.execute(intervals.update().where(intervals.c.age_min_days.is_(None)).values(age_min_days=0))

    op.drop_constraint("uq_biomarker_intervals_stratum", "biomarker_intervals", type_="unique")
    op.alter_column("biomarker_intervals", "sex", existing_type=sa.String(6), nullable=False)
    op.alter_column(
        "biomarker_intervals",
        "age_min_days",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="0",
    )
    op.create_unique_constraint(
        "uq_biomarker_intervals_stratum",
        "biomarker_intervals",
        STRATUM_COLUMNS,
    )


def downgrade() -> None:
    op.drop_constraint("uq_biomarker_intervals_stratum", "biomarker_intervals", type_="unique")
    op.alter_column("biomarker_intervals", "sex", existing_type=sa.String(6), nullable=True)
    op.alter_column(
        "biomarker_intervals",
        "age_min_days",
        existing_type=sa.Integer(),
        nullable=True,
        server_default=None,
    )
    op.create_unique_constraint(
        "uq_biomarker_intervals_stratum",
        "biomarker_intervals",
        [*STRATUM_COLUMNS, "age_max_days"],
    )
