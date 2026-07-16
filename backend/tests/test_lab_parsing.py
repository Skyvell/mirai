from datetime import date
from decimal import Decimal

from mirai_api.models import Biomarker
from mirai_api.services.lab_parsing import (
    ExtractedMeasurement,
    LabExtraction,
    UnmatchedMarker,
    map_extraction,
)


def _catalogue() -> list[Biomarker]:
    return [
        Biomarker(
            slug="ldl_cholesterol",
            display_name="LDL Cholesterol",
            loinc_code="18262-6",
            canonical_unit="mmol/L",
            category="lipids",
        )
    ]


def test_known_slug_maps_to_row() -> None:
    extraction = LabExtraction(
        measured_at=date(2026, 1, 2),
        measurements=[
            ExtractedMeasurement(
                biomarker_slug="ldl_cholesterol",
                value=Decimal("3.1"),
                unit="mmol/L",
                reference_low=None,
                reference_high=Decimal("3.0"),
            )
        ],
        unmatched=[],
    )
    mapped, skipped = map_extraction(extraction, _catalogue())
    assert len(mapped) == 1
    assert not skipped
    row = mapped[0]
    assert row.biomarker.slug == "ldl_cholesterol"
    assert row.measurement.value == Decimal("3.1")
    assert row.measurement.reference_low is None
    assert row.measurement.reference_high == Decimal("3.0")


def test_unknown_slug_is_demoted_to_skipped() -> None:
    extraction = LabExtraction(
        measured_at=None,
        measurements=[
            ExtractedMeasurement(
                biomarker_slug="not_a_real_slug",
                value=Decimal("1.0"),
                unit="mmol/L",
                reference_low=None,
                reference_high=None,
            )
        ],
        unmatched=[],
    )
    mapped, skipped = map_extraction(extraction, _catalogue())
    assert not mapped
    assert len(skipped) == 1
    assert skipped[0].reason == "unknown_slug"
    assert skipped[0].name == "not_a_real_slug"


def test_unmatched_markers_pass_through() -> None:
    extraction = LabExtraction(
        measured_at=None,
        measurements=[],
        unmatched=[
            UnmatchedMarker(
                name="Exotic Marker",
                value="42",
                unit="ng/mL",
                reference_low=Decimal("10"),
                reference_high=Decimal("50"),
            )
        ],
    )
    mapped, skipped = map_extraction(extraction, _catalogue())
    assert not mapped
    assert len(skipped) == 1
    assert skipped[0].reason == "unmatched"
    assert skipped[0].name == "Exotic Marker"
    # The reference range is carried through so the user can keep it on mapping.
    assert skipped[0].reference_low == Decimal("10")
    assert skipped[0].reference_high == Decimal("50")
