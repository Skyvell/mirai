from decimal import Decimal
from typing import Self

from pydantic import BaseModel, RootModel

from mirai_api.core.enums import IntervalType, Sex
from mirai_api.models import BiomarkerInterval


class BiomarkerIntervalRead(BaseModel):
    type: IntervalType
    sex: Sex | None
    age_min_days: int | None
    age_max_days: int | None
    low: Decimal | None
    high: Decimal | None

    @classmethod
    def from_interval(cls, interval: BiomarkerInterval) -> Self:
        """The columns are interval_low/interval_high; the wire names are low/high."""
        return cls(
            type=interval.type,
            sex=interval.sex,
            age_min_days=interval.age_min_days,
            age_max_days=interval.age_max_days,
            low=interval.interval_low,
            high=interval.interval_high,
        )


class BiomarkerIntervalsBySlug(RootModel[dict[str, list[BiomarkerIntervalRead]]]):
    """Canonical interval bands keyed by biomarker slug; the GET /biomarker-intervals payload."""

    @classmethod
    def from_intervals(cls, intervals: list[BiomarkerInterval]) -> Self:
        """Requires an eager-loaded `biomarker`; the relationship is lazy="raise"."""
        bands_by_slug: dict[str, list[BiomarkerIntervalRead]] = {}
        for interval in intervals:
            slug = interval.biomarker.slug
            if slug not in bands_by_slug:
                bands_by_slug[slug] = []
            bands_by_slug[slug].append(BiomarkerIntervalRead.from_interval(interval))

        return cls(bands_by_slug)
