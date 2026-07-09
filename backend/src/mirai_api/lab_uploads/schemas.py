import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from mirai_api.lab_uploads.parsing import SkippedMarker


class MeasurementOut(BaseModel):
    biomarker_slug: str
    display_name: str
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None


class LabUploadResponse(BaseModel):
    upload_id: uuid.UUID
    measured_at: date | None
    measurements: list[MeasurementOut]
    skipped: list[SkippedMarker]
