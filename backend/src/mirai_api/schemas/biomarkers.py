from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class MeasurementPoint(BaseModel):
    measured_at: date | None
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None


class CatalogBiomarker(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    display_name: str
    category: str
    canonical_unit: str


class BiomarkerSeries(CatalogBiomarker):
    measurements: list[MeasurementPoint]


class MeasurementCreate(BaseModel):
    # Bounded to the column type Numeric(12, 4) so overflow is a 422, not a 500.
    value: Annotated[Decimal, Field(max_digits=12, decimal_places=4)]
    # Verbatim unit; defaults to the biomarker's canonical_unit when omitted.
    unit: str | None = None
    measured_at: date


class MeasurementCreated(BaseModel):
    display_name: str
    value: Decimal
    unit: str
