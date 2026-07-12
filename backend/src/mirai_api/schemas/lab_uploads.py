import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from mirai_api.core.enums import UploadStatus
from mirai_api.services.lab_parsing import SkippedMarker


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


class LabUploadSummary(BaseModel):
    id: uuid.UUID
    filename: str
    status: UploadStatus
    parsed_at: datetime | None
    created_at: datetime
    measurement_count: int
