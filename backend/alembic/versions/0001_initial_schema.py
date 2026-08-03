"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-03 00:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from mirai_api.seed.biomarker_intervals import INTERVALS
from mirai_api.seed.biomarkers import BIOMARKERS

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "biomarkers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("loinc_code", sa.Text(), nullable=True),
        sa.Column("canonical_unit", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_biomarkers")),
        sa.UniqueConstraint("slug", name=op.f("uq_biomarkers_slug")),
    )
    op.create_index(op.f("ix_biomarkers_loinc_code"), "biomarkers", ["loinc_code"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("clerk_user_id", sa.Text(), nullable=False),
        sa.Column(
            "sex",
            sa.Enum("male", "female", name="sex", native_enum=False, create_constraint=True),
            nullable=True,
        ),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("clerk_user_id", name=op.f("uq_users_clerk_user_id")),
    )

    op.create_table(
        "lab_uploads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "processing",
                "awaiting_review",
                "confirmed",
                "failed",
                name="lab_upload_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("measured_at", sa.Date(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_lab_uploads_users_user_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lab_uploads")),
    )
    op.create_index(op.f("ix_lab_uploads_content_sha256"), "lab_uploads", ["content_sha256"])
    op.create_index(op.f("ix_lab_uploads_user_id"), "lab_uploads", ["user_id"])

    op.create_table(
        "biomarker_measurements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("biomarker_id", sa.Uuid(), nullable=False),
        sa.Column("lab_upload_id", sa.Uuid(), nullable=True),
        sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("reference_low", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("reference_high", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("measured_at", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["biomarker_id"],
            ["biomarkers.id"],
            name=op.f("fk_biomarker_measurements_biomarkers_biomarker_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["lab_upload_id"],
            ["lab_uploads.id"],
            name=op.f("fk_biomarker_measurements_lab_uploads_lab_upload_id"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_biomarker_measurements_users_user_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_biomarker_measurements")),
    )
    op.create_index(
        op.f("ix_biomarker_measurements_lab_upload_id"),
        "biomarker_measurements",
        ["lab_upload_id"],
    )
    op.create_index(
        "ix_biomarker_measurements_user_series",
        "biomarker_measurements",
        ["user_id", "biomarker_id", "measured_at"],
    )

    op.create_table(
        "lab_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lab_upload_id", sa.Uuid(), nullable=False),
        sa.Column("biomarker_id", sa.Uuid(), nullable=True),
        sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("reference_low", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("reference_high", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("source_name", sa.Text(), nullable=True),
        sa.Column("included", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["biomarker_id"],
            ["biomarkers.id"],
            name=op.f("fk_lab_results_biomarkers_biomarker_id"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["lab_upload_id"],
            ["lab_uploads.id"],
            name=op.f("fk_lab_results_lab_uploads_lab_upload_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lab_results")),
    )
    op.create_index(op.f("ix_lab_results_lab_upload_id"), "lab_results", ["lab_upload_id"])

    op.create_table(
        "biomarker_intervals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("biomarker_id", sa.Uuid(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "reference",
                "optimal",
                name="biomarker_interval_type",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="reference",
            nullable=False,
        ),
        sa.Column(
            "sex",
            sa.Enum("male", "female", name="sex", native_enum=False, create_constraint=True),
            nullable=True,
        ),
        sa.Column("age_min_days", sa.Integer(), nullable=True),
        sa.Column("age_max_days", sa.Integer(), nullable=True),
        sa.Column("interval_low", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("interval_high", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["biomarker_id"],
            ["biomarkers.id"],
            name=op.f("fk_biomarker_intervals_biomarkers_biomarker_id"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_biomarker_intervals")),
        sa.UniqueConstraint(
            "biomarker_id",
            "type",
            "sex",
            "age_min_days",
            "age_max_days",
            name="uq_biomarker_intervals_stratum",
        ),
        sa.CheckConstraint(
            "interval_low IS NOT NULL OR interval_high IS NOT NULL",
            name=op.f("ck_biomarker_intervals_one_sided_or_bounded"),
        ),
        sa.CheckConstraint(
            "interval_low IS NULL OR interval_high IS NULL OR interval_low <= interval_high",
            name=op.f("ck_biomarker_intervals_low_not_above_high"),
        ),
        sa.CheckConstraint(
            "age_min_days IS NULL OR age_max_days IS NULL OR age_min_days < age_max_days",
            name=op.f("ck_biomarker_intervals_age_min_below_max"),
        ),
    )

    # Seed the read-only biomarker catalogue; keep the ids to link intervals below.
    biomarker_ids = {biomarker["slug"]: uuid.uuid7() for biomarker in BIOMARKERS}
    biomarkers = sa.table(
        "biomarkers",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.Text()),
        sa.column("display_name", sa.Text()),
        sa.column("loinc_code", sa.Text()),
        sa.column("canonical_unit", sa.Text()),
        sa.column("category", sa.Text()),
    )
    op.bulk_insert(
        biomarkers,
        [
            {
                "id": biomarker_ids[biomarker["slug"]],
                "slug": biomarker["slug"],
                "display_name": biomarker["display_name"],
                "loinc_code": biomarker["loinc_code"],
                "canonical_unit": biomarker["canonical_unit"],
                "category": biomarker["category"],
            }
            for biomarker in BIOMARKERS
        ],
    )

    # Seed the canonical reference intervals (Karolinska); INTERVALS is keyed by slug.
    biomarker_intervals = sa.table(
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
    op.bulk_insert(
        biomarker_intervals,
        [
            {
                "id": uuid.uuid7(),
                "biomarker_id": biomarker_ids[band["slug"]],
                "type": "reference",
                "sex": band["sex"],
                "age_min_days": band["age_min_days"],
                "age_max_days": band["age_max_days"],
                "interval_low": band["low"],
                "interval_high": band["high"],
                "source": band["source"],
                "source_url": band["source_url"],
            }
            for band in INTERVALS
        ],
    )


def downgrade() -> None:
    op.drop_table("biomarker_intervals")
    op.drop_index(op.f("ix_lab_results_lab_upload_id"), table_name="lab_results")
    op.drop_table("lab_results")
    op.drop_index("ix_biomarker_measurements_user_series", table_name="biomarker_measurements")
    op.drop_index(
        op.f("ix_biomarker_measurements_lab_upload_id"),
        table_name="biomarker_measurements",
    )
    op.drop_table("biomarker_measurements")
    op.drop_index(op.f("ix_lab_uploads_user_id"), table_name="lab_uploads")
    op.drop_index(op.f("ix_lab_uploads_content_sha256"), table_name="lab_uploads")
    op.drop_table("lab_uploads")
    op.drop_table("users")
    op.drop_index(op.f("ix_biomarkers_loinc_code"), table_name="biomarkers")
    op.drop_table("biomarkers")
