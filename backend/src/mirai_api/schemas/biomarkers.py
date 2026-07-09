from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class MeasurementPoint(BaseModel):
    measured_at: date | None
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None


class BiomarkerSeries(BaseModel):
    slug: str
    display_name: str
    category: str
    canonical_unit: str
    measurements: list[MeasurementPoint]
