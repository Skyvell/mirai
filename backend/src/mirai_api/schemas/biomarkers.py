from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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
    value: Decimal
    # Verbatim unit; defaults to the biomarker's canonical_unit when omitted.
    unit: str | None = None
    measured_at: date


class MeasurementCreated(BaseModel):
    biomarker_slug: str
    display_name: str
    value: Decimal
    unit: str
    measured_at: date
