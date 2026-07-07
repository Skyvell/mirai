"""create biomarker tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-07 15:10:00.000000

"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Seed catalogue: (slug, display_name, loinc_code, canonical_unit, category).
# canonical_unit is UCUM (SI/EU convention). loinc_code is best-effort and must
# be verified against the official LOINC release before any real lab
# integration relies on it — the column is nullable for exactly that backfill.
_CATALOGUE: list[tuple[str, str, str | None, str, str]] = [
    # Lipids.
    ("total_cholesterol", "Total Cholesterol", "2093-3", "mmol/L", "lipids"),
    ("ldl_cholesterol", "LDL Cholesterol", "18262-6", "mmol/L", "lipids"),
    ("hdl_cholesterol", "HDL Cholesterol", "2085-9", "mmol/L", "lipids"),
    ("triglycerides", "Triglycerides", "2571-8", "mmol/L", "lipids"),
    ("apolipoprotein_b", "Apolipoprotein B", "1884-6", "g/L", "lipids"),
    ("lipoprotein_a", "Lipoprotein(a)", "43583-4", "nmol/L", "lipids"),
    # Metabolic.
    ("glucose", "Glucose (Fasting)", "1558-6", "mmol/L", "metabolic"),
    ("hba1c", "HbA1c", "4548-4", "%", "metabolic"),
    ("insulin", "Insulin (Fasting)", "20448-7", "m[IU]/L", "metabolic"),
    # Hematology.
    ("hemoglobin", "Hemoglobin", "718-7", "g/L", "hematology"),
    ("hematocrit", "Hematocrit", "4544-3", "%", "hematology"),
    ("wbc", "White Blood Cell Count", "6690-2", "10*9/L", "hematology"),
    ("rbc", "Red Blood Cell Count", "789-8", "10*12/L", "hematology"),
    ("platelets", "Platelet Count", "777-3", "10*9/L", "hematology"),
    ("mcv", "Mean Corpuscular Volume", "787-2", "fL", "hematology"),
    ("mch", "Mean Corpuscular Hemoglobin", "785-6", "pg", "hematology"),
    ("mchc", "Mean Corpuscular Hemoglobin Concentration", "786-4", "g/L", "hematology"),
    # Liver.
    ("alt", "Alanine Aminotransferase (ALT)", "1742-6", "U/L", "liver"),
    ("ast", "Aspartate Aminotransferase (AST)", "1920-8", "U/L", "liver"),
    ("alp", "Alkaline Phosphatase", "6768-6", "U/L", "liver"),
    ("ggt", "Gamma-Glutamyl Transferase", "2324-2", "U/L", "liver"),
    ("total_bilirubin", "Total Bilirubin", "1975-2", "umol/L", "liver"),
    ("albumin", "Albumin", "1751-7", "g/L", "liver"),
    # Kidney.
    ("creatinine", "Creatinine", "2160-0", "umol/L", "kidney"),
    ("egfr", "Estimated GFR", "33914-3", "mL/min/{1.73_m2}", "kidney"),
    ("urea", "Urea", "22664-7", "mmol/L", "kidney"),
    ("cystatin_c", "Cystatin C", "33863-2", "mg/L", "kidney"),
    ("uric_acid", "Uric Acid", "14933-6", "umol/L", "kidney"),
    # Thyroid.
    ("tsh", "Thyroid-Stimulating Hormone", "3016-3", "m[IU]/L", "thyroid"),
    ("free_t4", "Free Thyroxine (fT4)", "3024-7", "pmol/L", "thyroid"),
    ("free_t3", "Free Triiodothyronine (fT3)", "3051-0", "pmol/L", "thyroid"),
    # Hormones.
    ("testosterone", "Testosterone (Total)", "2986-8", "nmol/L", "hormones"),
    ("free_testosterone", "Free Testosterone", "2991-8", "pmol/L", "hormones"),
    ("estradiol", "Estradiol", "2243-4", "pmol/L", "hormones"),
    ("cortisol", "Cortisol", "2143-6", "nmol/L", "hormones"),
    ("shbg", "Sex Hormone-Binding Globulin", "13967-5", "nmol/L", "hormones"),
    ("dhea_s", "DHEA-Sulfate", "2191-5", "umol/L", "hormones"),
    # Inflammation.
    ("hs_crp", "High-Sensitivity C-Reactive Protein", "30522-7", "mg/L", "inflammation"),
    ("homocysteine", "Homocysteine", "13965-9", "umol/L", "inflammation"),
    # Vitamins.
    ("vitamin_d", "25-Hydroxyvitamin D", "62292-8", "nmol/L", "vitamins"),
    ("vitamin_b12", "Vitamin B12", "2132-9", "pmol/L", "vitamins"),
    ("folate", "Folate", "2284-8", "nmol/L", "vitamins"),
    # Iron.
    ("ferritin", "Ferritin", "2276-4", "ug/L", "iron"),
    ("iron", "Iron", "2498-4", "umol/L", "iron"),
    ("transferrin", "Transferrin", "3034-6", "g/L", "iron"),
    ("transferrin_saturation", "Transferrin Saturation", "2502-3", "%", "iron"),
    # Electrolytes.
    ("sodium", "Sodium", "2951-2", "mmol/L", "electrolytes"),
    ("potassium", "Potassium", "2823-3", "mmol/L", "electrolytes"),
    ("chloride", "Chloride", "2075-0", "mmol/L", "electrolytes"),
    ("bicarbonate", "Bicarbonate", "1963-8", "mmol/L", "electrolytes"),
    ("calcium", "Calcium (Total)", "17861-6", "mmol/L", "electrolytes"),
    ("magnesium", "Magnesium", "19123-9", "mmol/L", "electrolytes"),
    ("phosphate", "Phosphate", "2777-1", "mmol/L", "electrolytes"),
    ("zinc", "Zinc", "5763-8", "umol/L", "electrolytes"),
]


def upgrade() -> None:
    op.create_table(
        "biomarkers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("loinc_code", sa.Text(), nullable=True),
        sa.Column("canonical_unit", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_biomarkers_loinc_code", "biomarkers", ["loinc_code"])

    op.create_table(
        "lab_uploads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "uploaded",
                "parsed",
                "failed",
                name="lab_upload_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_lab_uploads_user_id", "lab_uploads", ["user_id"])

    op.create_table(
        "biomarker_measurements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("biomarker_id", sa.Uuid(), nullable=False),
        sa.Column("lab_upload_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.Numeric(12, 4), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("reference_low", sa.Numeric(12, 4), nullable=True),
        sa.Column("reference_high", sa.Numeric(12, 4), nullable=True),
        sa.Column("measured_at", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["biomarker_id"], ["biomarkers.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["lab_upload_id"], ["lab_uploads.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_biomarker_measurements_lab_upload_id",
        "biomarker_measurements",
        ["lab_upload_id"],
    )
    op.create_index(
        "ix_biomarker_measurements_user_series",
        "biomarker_measurements",
        ["user_id", "biomarker_id", "measured_at"],
    )

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
                "id": uuid.uuid7(),
                "slug": slug,
                "display_name": display_name,
                "loinc_code": loinc_code,
                "canonical_unit": canonical_unit,
                "category": category,
            }
            for slug, display_name, loinc_code, canonical_unit, category in _CATALOGUE
        ],
    )


def downgrade() -> None:
    op.drop_table("biomarker_measurements")
    op.drop_table("lab_uploads")
    op.drop_index("ix_biomarkers_loinc_code", table_name="biomarkers")
    op.drop_table("biomarkers")
