from decimal import Decimal

from pydantic import BaseModel

from mirai_api.core.enums import IntervalType, Sex
from mirai_api.schemas.biomarkers import BiomarkerRead


class BiomarkerIntervalRead(BaseModel):
    type: IntervalType
    sex: Sex | None
    age_min_days: int | None
    age_max_days: int | None
    low: Decimal | None
    high: Decimal | None


class BiomarkerIntervalsRead(BiomarkerRead):
    intervals: list[BiomarkerIntervalRead]
