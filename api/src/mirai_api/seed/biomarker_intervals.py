"""Seed data for `biomarker_intervals`, imported by the 0001 migration.

Each ``Curve`` is one (biomarker, sex) series of ``(from_age_days, low, high)``
bands, sorted by age. A band covers the half-open age range
``[from_age_days, next from_age_days)``; the last band is open-ended. Ages below
the first band have no interval. ``low`` and ``high`` are inclusive; either may
be ``None`` for a one-sided interval.

Values are Karolinska Universitetslaboratoriet referensintervall in the
biomarker's canonical unit. Years/months have no fixed day count, so the
helpers approximate (1 y = 365.25 d, 1 mo = 30.4375 d).
"""

from dataclasses import dataclass
from decimal import Decimal
from itertools import pairwise

from mirai_api.core.enums import IntervalType, Sex

SOURCE = "Karolinska Universitetslaboratoriet"

MALE = Sex.MALE
FEMALE = Sex.FEMALE


def years(n: float) -> int:
    return round(n * 365.25)


def months(n: float) -> int:
    return round(n * 30.4375)


def weeks(n: float) -> int:
    return round(n * 7)


def days(n: int) -> int:
    return n


GLUCOSE_URL = "https://www.karolinska.se/KUL/Alla-anvisningar/Anvisning/9095"
CHOLESTEROL_URL = "https://www.karolinska.se/pta/klinisk-kemi/kolesterol-p-/"
LDL_URL = "https://www.karolinska.se/pta/klinisk-kemi/ldl-kolesterol-fp-/"
HDL_URL = "https://www.karolinska.se/pta/klinisk-kemi/hdl-kolesterol-p-/"
TRIGLYCERIDES_URL = "https://www.karolinska.se/pta/klinisk-kemi/triglycerid-fp-/"
HBA1C_URL = "https://www.karolinska.se/KUL/Alla-anvisningar/Anvisning/9104"
TSH_URL = "https://www.karolinska.se/KUL/Alla-anvisningar/Anvisning/9311"
HEMOGLOBIN_URL = "https://www.karolinska.se/KUL/Alla-anvisningar/Anvisning/9112"
FERRITIN_URL = "https://www.karolinska.se/KUL/Alla-anvisningar/Anvisning/9074"
CREATININE_URL = "https://www.karolinska.se/KUL/Alla-anvisningar/Anvisning/9168"


type Band = tuple[int, str | None, str | None]


@dataclass(frozen=True)
class Curve:
    slug: str
    sex: Sex
    source_url: str
    bands: list[Band]
    type: IntervalType = IntervalType.REFERENCE


# fmt: off
CURVES: list[Curve] = [
    Curve("glucose", MALE, GLUCOSE_URL, [
        (0,          "4.2",  "6.0"),
    ]),
    Curve("glucose", FEMALE, GLUCOSE_URL, [
        (0,          "4.2",  "6.0"),
    ]),

    Curve("total_cholesterol", MALE, CHOLESTEROL_URL, [
        (0,          "2.4",  "5.3"),
        (years(1),   "2.7",  "5.9"),
        (years(15),  "2.5",  "5.4"),
        (years(18),  "2.9",  "6.1"),
        (years(31),  "3.3",  "6.9"),
        (years(51),  "3.9",  "7.8"),
    ]),
    Curve("total_cholesterol", FEMALE, CHOLESTEROL_URL, [
        (0,          "2.4",  "5.3"),
        (years(1),   "2.7",  "5.9"),
        (years(15),  "2.4",  "6.0"),
        (years(18),  "2.9",  "6.1"),
        (years(31),  "3.3",  "6.9"),
        (years(51),  "3.9",  "7.8"),
    ]),

    Curve("ldl_cholesterol", MALE, LDL_URL, [
        (0,          "0.8",  "3.5"),
        (years(1),   "1.3",  "4.0"),
        (years(18),  "1.2",  "4.3"),
        (years(31),  "1.4",  "4.7"),
        (years(51),  "2.0",  "5.3"),
    ]),
    Curve("ldl_cholesterol", FEMALE, LDL_URL, [
        (0,          "0.8",  "3.5"),
        (years(1),   "1.3",  "4.0"),
        (years(18),  "1.2",  "4.3"),
        (years(31),  "1.4",  "4.7"),
        (years(51),  "2.0",  "5.3"),
    ]),

    Curve("hdl_cholesterol", MALE, HDL_URL, [
        (0,          "0.7",  "1.9"),
        (years(15),  "0.7",  "1.8"),
        (years(18),  "0.8",  "2.1"),
    ]),
    Curve("hdl_cholesterol", FEMALE, HDL_URL, [
        (0,          "0.7",  "1.9"),
        (years(15),  "0.6",  "2.2"),
        (years(18),  "1.0",  "2.7"),
    ]),

    Curve("triglycerides", MALE, TRIGLYCERIDES_URL, [
        (0,          "0.59", "2.6"),
        (years(1),   "0.43", "2.8"),
        (years(18),  "0.45", "2.6"),
    ]),
    Curve("triglycerides", FEMALE, TRIGLYCERIDES_URL, [
        (0,          "0.59", "2.6"),
        (years(1),   "0.43", "2.8"),
        (years(18),  "0.45", "2.6"),
    ]),

    Curve("hba1c", MALE, HBA1C_URL, [
        (0,          "27",   "42"),
        (years(50),  "31",   "46"),
    ]),
    Curve("hba1c", FEMALE, HBA1C_URL, [
        (0,          "27",   "42"),
        (years(50),  "31",   "46"),
    ]),

    Curve("tsh", MALE, TSH_URL, [
        (0,          "0.7",  "15"),
        (weeks(1),   "0.7",  "11"),
        (months(4),  "0.7",  "8.4"),
        (years(1),   "0.7",  "6.0"),
        (years(7),   "0.6",  "4.8"),
        (years(12),  "0.5",  "4.3"),
        (years(19),  "0.3",  "4.2"),
    ]),
    Curve("tsh", FEMALE, TSH_URL, [
        (0,          "0.7",  "15"),
        (weeks(1),   "0.7",  "11"),
        (months(4),  "0.7",  "8.4"),
        (years(1),   "0.7",  "6.0"),
        (years(7),   "0.6",  "4.8"),
        (years(12),  "0.5",  "4.3"),
        (years(19),  "0.3",  "4.2"),
    ]),

    Curve("hemoglobin", MALE, HEMOGLOBIN_URL, [
        (0,          "150",  "240"),
        (days(2),    "140",  "220"),
        (days(7),    "130",  "200"),
        (days(22),   "100",  "180"),
        (months(1),  "100",  "160"),
        (months(4),  "100",  "140"),
        (years(1),   "100",  "150"),
        (years(7),   "105",  "150"),
        (years(11),  "110",  "160"),
        (years(18),  "134",  "170"),
    ]),
    Curve("hemoglobin", FEMALE, HEMOGLOBIN_URL, [
        (0,          "150",  "240"),
        (days(2),    "140",  "220"),
        (days(7),    "130",  "200"),
        (days(22),   "100",  "180"),
        (months(1),  "100",  "160"),
        (months(4),  "100",  "140"),
        (years(1),   "100",  "150"),
        (years(7),   "105",  "150"),
        (years(11),  "110",  "160"),
        (years(18),  "117",  "153"),
    ]),

    Curve("ferritin", MALE, FERRITIN_URL, [
        (years(18),  "30",   "400"),
    ]),
    Curve("ferritin", FEMALE, FERRITIN_URL, [
        (years(18),  "13",   "150"),
    ]),

    Curve("creatinine", MALE, CREATININE_URL, [
        (0,          None,   "77"),
        (days(15),   None,   "60"),
        (months(2),  None,   "41"),
        (years(3),   None,   "44"),
        (years(4),   None,   "47"),
        (years(5),   None,   "50"),
        (years(6),   None,   "53"),
        (years(7),   None,   "56"),
        (years(8),   None,   "59"),
        (years(9),   None,   "62"),
        (years(10),  None,   "65"),
        (years(11),  None,   "68"),
        (years(12),  None,   "71"),
        (years(13),  None,   "84"),
        (years(14),  None,   "87"),
        (years(15),  None,   "90"),
        (years(16),  None,   "93"),
        (years(17),  None,   "96"),
        (years(18),  None,   "100"),
    ]),
    Curve("creatinine", FEMALE, CREATININE_URL, [
        (0,          None,   "77"),
        (days(15),   None,   "60"),
        (months(2),  None,   "41"),
        (years(3),   None,   "44"),
        (years(4),   None,   "47"),
        (years(5),   None,   "50"),
        (years(6),   None,   "53"),
        (years(7),   None,   "56"),
        (years(8),   None,   "59"),
        (years(9),   None,   "62"),
        (years(10),  None,   "65"),
        (years(11),  None,   "68"),
        (years(12),  None,   "71"),
        (years(13),  None,   "74"),
        (years(14),  None,   "77"),
        (years(15),  None,   "80"),
        (years(16),  None,   "83"),
        (years(17),  None,   "86"),
        (years(18),  None,   "90"),
    ]),
]
# fmt: on


def parse_bound(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


def validate_curve(curve: Curve) -> None:
    label = f"{curve.slug} ({curve.sex})"
    starts = [start for start, _, _ in curve.bands]

    if not starts:
        raise ValueError(f"{label}: no bands")
    if starts[0] < 0:
        raise ValueError(f"{label}: first band starts below 0")
    if any(left >= right for left, right in pairwise(starts)):
        raise ValueError(f"{label}: band starts must strictly increase")

    for start, low, high in curve.bands:
        if low is None and high is None:
            raise ValueError(f"{label}: band at {start} has no bound")
        if low is not None and high is not None and Decimal(low) > Decimal(high):
            raise ValueError(f"{label}: band at {start} has low above high")


def expand_curve(curve: Curve) -> list[dict]:
    validate_curve(curve)

    ends = [start for start, _, _ in curve.bands[1:]] + [None]
    return [
        {
            "slug": curve.slug,
            "type": curve.type,
            "sex": curve.sex,
            "age_min_days": start,
            "age_max_days": end,
            "low": parse_bound(low),
            "high": parse_bound(high),
            "source": SOURCE,
            "source_url": curve.source_url,
        }
        for (start, low, high), end in zip(curve.bands, ends, strict=True)
    ]


INTERVALS: list[dict] = [row for curve in CURVES for row in expand_curve(curve)]
