from collections import Counter
from itertools import pairwise

import pytest

from mirai_api.core.enums import Sex
from mirai_api.seed.biomarker_intervals import (
    CURVES,
    INTERVALS,
    Band,
    Curve,
    years,
)
from mirai_api.seed.biomarkers import BIOMARKERS


def _curve(bands: list[Band]) -> Curve:
    return Curve("glucose", Sex.MALE, "https://example.test", bands)


def test_seed_has_one_curve_per_stratum() -> None:
    strata = Counter((curve.slug, curve.type, curve.sex) for curve in CURVES)
    assert [stratum for stratum, count in strata.items() if count > 1] == []


def test_seed_slugs_exist_in_catalogue() -> None:
    catalogue = {biomarker["slug"] for biomarker in BIOMARKERS}
    assert {curve.slug for curve in CURVES} <= catalogue


def test_seed_rows_name_sex_and_start_age() -> None:
    assert all(row["sex"] in Sex for row in INTERVALS)
    assert all(row["age_min_days"] is not None for row in INTERVALS)


def test_build_rows_tiles_ages_without_gaps() -> None:
    rows = _curve(
        [(0, "4.0", "6.0"), (years(18), "4.2", None), (years(50), None, "6.5")]
    ).build_rows()

    assert [(row["age_min_days"], row["age_max_days"]) for row in rows] == [
        (0, years(18)),
        (years(18), years(50)),
        (years(50), None),
    ]
    assert all(left["age_max_days"] == right["age_min_days"] for left, right in pairwise(rows))


@pytest.mark.parametrize(
    ("bands", "message"),
    [
        ([], "no bands"),
        ([(-1, "4.0", "6.0")], "starts below 0"),
        ([(0, "4.0", "6.0"), (years(50), "4.0", "6.0"), (years(18), "4.0", "6.0")], "increase"),
        ([(0, "4.0", "6.0"), (0, "4.0", "6.0")], "increase"),
        ([(0, None, None)], "no bound"),
        ([(0, "6.0", "4.0")], "low above high"),
    ],
)
def test_curve_rejects_malformed_bands(bands: list[Band], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _curve(bands)
