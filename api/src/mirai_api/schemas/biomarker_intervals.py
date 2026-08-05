from decimal import Decimal

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
    def from_interval(cls, interval: BiomarkerInterval) -> BiomarkerIntervalRead:
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
