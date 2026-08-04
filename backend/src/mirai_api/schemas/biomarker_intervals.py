from decimal import Decimal

from pydantic import BaseModel, RootModel

from mirai_api.core.enums import IntervalType, Sex


class BiomarkerIntervalRead(BaseModel):
    type: IntervalType
    sex: Sex | None
    age_min_days: int | None
    age_max_days: int | None
    low: Decimal | None
    high: Decimal | None


class BiomarkerIntervalsBySlug(RootModel[dict[str, list[BiomarkerIntervalRead]]]):
    """Canonical interval bands keyed by biomarker slug; the GET /biomarker-intervals payload."""
