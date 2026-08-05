"""Generate the demo biomarker measurement dataset to testdata/biomarker_measurements.csv.

One synthetic subject — male, born 1991-08-18 — sampled roughly every four months from
birth to 2026-08-04, across all ten catalogue markers. Reference bounds are resolved from
the catalogue's own seed data, so the dataset cannot drift from the shipped intervals.

Values follow an age-dependent center plus AR(1) noise, so consecutive points correlate the
way repeated measurements of one person do. Out-of-range values are clustered into coherent
clinical episodes rather than scattered, which both reads as real and makes the out-of-range
render path meaningful to look at.

Deterministic: same seed, byte-identical CSV. Run rarely; the CSV is the committed artifact.

    uv run python scripts/demo_data/generate.py
"""

import csv
import random
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from itertools import pairwise
from pathlib import Path

import subject
from mirai_api.core.enums import IntervalType
from mirai_api.seed.biomarker_intervals import INTERVALS
from mirai_api.seed.biomarkers import BIOMARKERS

# Sampling starts at birth, so the series walks the full pediatric band ladder before
# reaching the adult intervals.
FIRST_MEASUREMENT = subject.DATE_OF_BIRTH
LAST_MEASUREMENT = date(2026, 8, 4)

# Roughly four months apart, jittered because real draws are not on a metronome.
CADENCE_DAYS = 122
JITTER_DAYS = 18

# The sampling grid and the value noise draw from separate streams, so changing the cadence
# does not perturb every value and vice versa.
SEED = 19910818

# AR(1) persistence: how strongly a point is pulled toward the previous one.
NOISE_PERSISTENCE = 0.55

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "testdata" / "biomarker_measurements.csv"

# Rows follow catalogue order; the sort below is the guard that keeps MARKERS aligned with it.
CATALOGUE_ORDER = {biomarker["slug"]: index for index, biomarker in enumerate(BIOMARKERS)}

CANONICAL_UNITS = {biomarker["slug"]: biomarker["canonical_unit"] for biomarker in BIOMARKERS}

FIELDNAMES = [
    "biomarker_slug",
    "measured_at",
    "value",
    "unit",
    "reference_low",
    "reference_high",
]


@dataclass(frozen=True)
class Marker:
    """A marker's value model: where it sits by age, how noisy it is, how it is reported."""

    slug: str

    # Age in years → central value, linearly interpolated between knots.
    knots: tuple[tuple[float, float], ...]

    # Relative sd of the multiplicative noise term.
    noise: float

    decimals: int

    # Slug whose noise state this marker reuses, making the two series co-move.
    correlates_with: str | None = None


@dataclass(frozen=True)
class Episode:
    """A sustained multiplicative excursion: ramps up, holds, then resolves.

    The plateau matters — with a single peak date the full effect lands between
    draws and no measurement ever shows it.
    """

    slugs: tuple[str, ...]

    start: date
    plateau_start: date
    plateau_end: date
    end: date

    # Multiplicative effect across the plateau, per slug in the same order.
    factors: tuple[float, ...]

    label: str = ""


@dataclass(frozen=True)
class Spike:
    """A single-draw excursion applied to the first measurement on or after ``on_or_after``."""

    slug: str
    on_or_after: date
    factor: float
    label: str = ""


MARKERS: tuple[Marker, ...] = (
    Marker(
        slug="total_cholesterol",
        knots=((0, 3.4), (1, 4.1), (5, 4.3), (12, 4.2), (16, 4.0), (18, 4.2), (35, 5.55)),
        noise=0.055,
        decimals=1,
    ),
    Marker(
        slug="ldl_cholesterol",
        knots=((0, 1.9), (1, 2.4), (5, 2.5), (12, 2.4), (16, 2.3), (18, 2.5), (35, 3.5)),
        noise=0.06,
        decimals=1,
        correlates_with="total_cholesterol",
    ),
    Marker(
        slug="hdl_cholesterol",
        knots=((0, 1.1), (1, 1.35), (5, 1.4), (12, 1.35), (16, 1.25), (18, 1.2), (35, 1.15)),
        noise=0.09,
        decimals=1,
    ),
    Marker(
        slug="triglycerides",
        knots=((0, 1.2), (1, 1.0), (5, 0.85), (12, 0.9), (18, 1.0), (35, 1.25)),
        noise=0.28,
        decimals=2,
    ),
    Marker(
        slug="glucose",
        knots=((0, 4.4), (1, 4.6), (12, 4.8), (18, 5.0), (35, 5.5)),
        noise=0.05,
        decimals=1,
    ),
    Marker(
        slug="hba1c",
        knots=((0, 30), (5, 31), (12, 32), (18, 33), (35, 38)),
        noise=0.045,
        decimals=0,
        correlates_with="glucose",
    ),
    Marker(
        slug="hemoglobin",
        knots=(
            (0, 195),
            (0.08, 150),
            (0.25, 108),
            (1, 122),
            (5, 126),
            (10, 132),
            (13, 138),
            (16, 148),
            (18, 150),
            (35, 152),
        ),
        noise=0.04,
        decimals=0,
    ),
    Marker(
        slug="tsh",
        knots=(
            (0, 6.5),
            (0.02, 5.0),
            (0.33, 3.4),
            (1, 3.0),
            (7, 2.6),
            (12, 2.2),
            (19, 1.9),
            (35, 2.0),
        ),
        noise=0.25,
        decimals=2,
    ),
    Marker(
        slug="creatinine",
        knots=(
            (0, 38),
            (0.04, 45),
            (0.5, 30),
            (3, 32),
            (5, 40),
            (8, 48),
            (10, 54),
            (12, 60),
            (14, 68),
            (16, 78),
            (18, 84),
            (25, 88),
            (35, 91),
        ),
        noise=0.05,
        decimals=0,
    ),
    Marker(
        slug="ferritin",
        knots=((0, 182), (0.5, 120), (1, 55), (5, 32), (12, 40), (18, 60), (25, 95), (35, 175)),
        noise=0.22,
        decimals=0,
    ),
)

METABOLIC_SLUGS = (
    "total_cholesterol",
    "ldl_cholesterol",
    "hdl_cholesterol",
    "triglycerides",
    "glucose",
    "hba1c",
)

EPISODES: tuple[Episode, ...] = (
    Episode(
        slugs=("hemoglobin",),
        start=date(1993, 1, 1),
        plateau_start=date(1993, 8, 1),
        plateau_end=date(1994, 6, 1),
        end=date(1995, 3, 1),
        factors=(0.76,),
        label="toddler iron-deficiency anemia",
    ),
    Episode(
        slugs=("ferritin", "hemoglobin"),
        start=date(2012, 6, 1),
        plateau_start=date(2013, 1, 1),
        plateau_end=date(2014, 1, 1),
        end=date(2014, 11, 1),
        factors=(0.22, 0.85),
        label="iron deficiency, resolving on supplementation",
    ),
    Episode(
        slugs=METABOLIC_SLUGS,
        start=date(2018, 9, 1),
        plateau_start=date(2019, 9, 1),
        plateau_end=date(2021, 3, 1),
        end=date(2022, 6, 1),
        factors=(1.38, 1.55, 0.67, 2.7, 1.18, 1.26),
        label="metabolic drift, then recovery",
    ),
    Episode(
        slugs=("tsh",),
        start=date(2022, 11, 1),
        plateau_start=date(2023, 4, 1),
        plateau_end=date(2024, 3, 1),
        end=date(2024, 10, 1),
        factors=(2.6,),
        label="subclinical thyroid blip",
    ),
    Episode(
        slugs=METABOLIC_SLUGS,
        start=date(2024, 9, 1),
        plateau_start=date(2025, 5, 1),
        plateau_end=LAST_MEASUREMENT,
        end=LAST_MEASUREMENT,
        factors=(1.3, 1.42, 0.72, 2.3, 1.15, 1.2),
        label="metabolic relapse, unresolved at the end of the series",
    ),
)

SPIKES: tuple[Spike, ...] = (
    Spike("triglycerides", date(2016, 3, 1), 2.8, "non-fasting draw"),
    Spike("triglycerides", date(2023, 6, 1), 2.8, "non-fasting draw"),
    Spike("creatinine", date(2025, 1, 1), 1.3, "dehydrated draw after exercise"),
)


def measurement_dates(rng: random.Random) -> list[date]:
    """Build the jittered ~4-month sampling grid, birth first."""
    dates = [FIRST_MEASUREMENT]

    step = 1
    while True:
        scheduled = FIRST_MEASUREMENT + timedelta(days=step * CADENCE_DAYS)
        if scheduled > LAST_MEASUREMENT:
            break

        # Jitter stays well under half a cadence, so the grid cannot reorder.
        drawn = scheduled + timedelta(days=rng.randint(-JITTER_DAYS, JITTER_DAYS))
        if drawn <= LAST_MEASUREMENT:
            dates.append(drawn)
        step += 1

    # Close the series on the requested end date when jitter left more than half a cadence.
    if (LAST_MEASUREMENT - dates[-1]).days >= CADENCE_DAYS // 2:
        dates.append(LAST_MEASUREMENT)

    return dates


def reference_band(
    slug: str,
    sex: str,
    age_days: int,
) -> tuple[Decimal | None, Decimal | None] | None:
    """Resolve the catalogue band for this marker at this age, or None when none applies."""
    for band in INTERVALS:
        if band["slug"] != slug:
            continue
        if band["sex"] not in (None, sex):
            continue

        # The stratum key includes type; only population reference bands belong in a row.
        if band.get("type", IntervalType.REFERENCE) != IntervalType.REFERENCE:
            continue

        # None on either bound means unbounded on that side.
        age_min = band["age_min_days"]
        age_max = band["age_max_days"]
        if age_min is not None and age_days < age_min:
            continue
        if age_max is not None and age_days >= age_max:
            continue

        return band["low"], band["high"]

    return None


def center(marker: Marker, age_years: float) -> float:
    """Interpolate the marker's central value at this age."""
    knots = marker.knots
    if age_years <= knots[0][0]:
        return knots[0][1]
    if age_years >= knots[-1][0]:
        return knots[-1][1]

    # The bounds above guarantee some pair brackets this age.
    for (left_age, left_value), (right_age, right_value) in pairwise(knots):
        if left_age <= age_years <= right_age:
            fraction = (age_years - left_age) / (right_age - left_age)
            return left_value + fraction * (right_value - left_value)

    raise AssertionError(f"knots do not cover age {age_years}")


def episode_factor(episode: Episode, slug: str, on: date) -> float:
    """Ramp in, hold across the plateau, ramp out; 1.0 outside the window."""
    if on < episode.start or on > episode.end or slug not in episode.slugs:
        return 1.0

    if on < episode.plateau_start:
        span = (episode.plateau_start - episode.start).days
        ramp = 1.0 if span == 0 else (on - episode.start).days / span
    elif on <= episode.plateau_end:
        ramp = 1.0
    else:
        span = (episode.end - episode.plateau_end).days
        ramp = 1.0 if span == 0 else (episode.end - on).days / span

    factor = episode.factors[episode.slugs.index(slug)]
    return 1.0 + (factor - 1.0) * ramp


def spike_factors(dates: list[date]) -> dict[tuple[str, date], float]:
    """Pin each spike to the first measurement on or after its target date."""
    resolved: dict[tuple[str, date], float] = {}
    for spike in SPIKES:
        for on in dates:
            if on >= spike.on_or_after:
                resolved[(spike.slug, on)] = spike.factor
                break

    return resolved


def noise_states(rng: random.Random, count: int) -> list[float]:
    """Draw a standardized AR(1) path: each step remembers the last."""
    innovation_scale = (1.0 - NOISE_PERSISTENCE**2) ** 0.5

    states = [rng.gauss(0.0, 1.0)]
    for _ in range(count - 1):
        states.append(NOISE_PERSISTENCE * states[-1] + innovation_scale * rng.gauss(0.0, 1.0))

    return states


def build_rows(dates: list[date]) -> list[dict[str, str]]:
    """Generate one row per marker per date, ordered by date then catalogue order."""
    rng = random.Random(SEED)
    spikes = spike_factors(dates)

    # One noise path per correlation group, so correlated markers co-move.
    paths: dict[str, list[float]] = {}
    for marker in MARKERS:
        group = marker.correlates_with or marker.slug
        if group not in paths:
            paths[group] = noise_states(rng, len(dates))

    ordered_markers = sorted(MARKERS, key=lambda marker: CATALOGUE_ORDER[marker.slug])

    rows: list[dict[str, str]] = []
    for index, on in enumerate(dates):
        age_days = (on - subject.DATE_OF_BIRTH).days
        age_years = age_days / 365.25

        for marker in ordered_markers:
            path = paths[marker.correlates_with or marker.slug]
            value = center(marker, age_years) * (1.0 + marker.noise * path[index])

            # Clinical episodes and single-draw excursions scale the point.
            for episode in EPISODES:
                value *= episode_factor(episode, marker.slug, on)
            value *= spikes.get((marker.slug, on), 1.0)

            band = reference_band(marker.slug, subject.SEX, age_days)
            low, high = band if band is not None else (None, None)
            rows.append(
                {
                    "biomarker_slug": marker.slug,
                    "measured_at": on.isoformat(),
                    "value": f"{max(value, 0.01):.{marker.decimals}f}",
                    "unit": CANONICAL_UNITS[marker.slug],
                    "reference_low": "" if low is None else str(low),
                    "reference_high": "" if high is None else str(high),
                }
            )

    return rows


def summarize(rows: list[dict[str, str]], dates: list[date]) -> None:
    """Print an audit of the dataset so it can be checked without opening the CSV."""
    print(f"{len(rows)} measurements over {len(dates)} dates")
    print(f"span {dates[0].isoformat()} → {dates[-1].isoformat()}")

    counted: Counter[str] = Counter()
    out_of_range: Counter[str] = Counter()
    no_band: Counter[str] = Counter()
    for row in rows:
        value = Decimal(row["value"])
        low = Decimal(row["reference_low"]) if row["reference_low"] else None
        high = Decimal(row["reference_high"]) if row["reference_high"] else None

        counted[row["biomarker_slug"]] += 1
        if low is None and high is None:
            no_band[row["biomarker_slug"]] += 1
        elif (low is not None and value < low) or (high is not None and value > high):
            out_of_range[row["biomarker_slug"]] += 1

    total_out = sum(out_of_range.values())
    print(f"out of range: {total_out} ({total_out / len(rows):.1%})")
    for biomarker in BIOMARKERS:
        slug = biomarker["slug"]
        print(
            f"  {slug:<18} {counted[slug]:>4} rows  "
            f"{out_of_range[slug]:>3} out of range  {no_band[slug]:>3} without a band"
        )

    # Name the excursions, so the audit says what the out-of-range values represent.
    print("episodes:")
    for episode in EPISODES:
        window = f"{episode.start.isoformat()} → {episode.end.isoformat()}"
        print(f"  {window}  {episode.label}")
    for spike in SPIKES:
        print(f"  {spike.on_or_after.isoformat()} onwards  {spike.slug}: {spike.label}")


def main() -> None:
    dates = measurement_dates(random.Random(SEED))
    rows = build_rows(dates)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    summarize(rows, dates)
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
