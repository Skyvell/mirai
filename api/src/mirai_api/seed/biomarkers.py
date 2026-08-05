"""Seed data for the `biomarkers` catalogue, imported by the 0001 migration.

Extend this by appending dicts to ``BIOMARKERS`` — each is one catalogue entry,
keyed by ``slug`` (the stable internal key the LLM maps to). ``canonical_unit``
is UCUM (SI/EU convention). ``loinc_code`` is the moles/volume (SCnc) variant
wherever the unit is molar (mmol/L, µmol/L) — LOINC uses distinct codes for
mass vs molar concentration, so the code must match the unit's property.

Scope is the markers that have canonical reference intervals (see
``biomarker_intervals.py``); keep the two files' slug sets aligned.
"""

BIOMARKERS: list[dict] = [
    # Lipids.
    {
        "slug": "total_cholesterol",
        "display_name": "Total Cholesterol",
        "loinc_code": "14647-2",
        "canonical_unit": "mmol/L",
        "category": "lipids",
    },
    {
        "slug": "ldl_cholesterol",
        "display_name": "LDL Cholesterol",
        "loinc_code": "22748-8",
        "canonical_unit": "mmol/L",
        "category": "lipids",
    },
    {
        "slug": "hdl_cholesterol",
        "display_name": "HDL Cholesterol",
        "loinc_code": "14646-4",
        "canonical_unit": "mmol/L",
        "category": "lipids",
    },
    {
        "slug": "triglycerides",
        "display_name": "Triglycerides",
        "loinc_code": "14927-8",
        "canonical_unit": "mmol/L",
        "category": "lipids",
    },
    # Metabolic.
    {
        "slug": "glucose",
        "display_name": "Glucose (Fasting)",
        "loinc_code": "14771-0",
        "canonical_unit": "mmol/L",
        "category": "metabolic",
    },
    {
        "slug": "hba1c",
        "display_name": "HbA1c",
        "loinc_code": "59261-8",
        "canonical_unit": "mmol/mol",
        "category": "metabolic",
    },
    # Hematology.
    {
        "slug": "hemoglobin",
        "display_name": "Hemoglobin",
        "loinc_code": "718-7",
        "canonical_unit": "g/L",
        "category": "hematology",
    },
    # Thyroid.
    {
        "slug": "tsh",
        "display_name": "Thyroid-Stimulating Hormone",
        "loinc_code": "3016-3",
        "canonical_unit": "m[IU]/L",
        "category": "thyroid",
    },
    # Kidney.
    {
        "slug": "creatinine",
        "display_name": "Creatinine",
        "loinc_code": "14682-9",
        "canonical_unit": "umol/L",
        "category": "kidney",
    },
    # Iron.
    {
        "slug": "ferritin",
        "display_name": "Ferritin",
        "loinc_code": "2276-4",
        "canonical_unit": "ug/L",
        "category": "iron",
    },
]
