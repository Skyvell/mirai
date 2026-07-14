import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from mirai_api.core.enums import UploadStatus


class LabUploadSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: UploadStatus
    parsed_at: datetime | None
    created_at: datetime
    measurement_count: int


class LabDraftItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # Null for a marker the parser could not map to the catalogue.
    biomarker_slug: str | None
    display_name: str | None
    value: Decimal | None
    raw_value: str | None
    unit: str | None
    reference_low: Decimal | None
    reference_high: Decimal | None
    source_name: str | None
    skip_reason: str | None
    included: bool


class LabDraft(BaseModel):
    measured_at: date | None
    items: list[LabDraftItemRead]
    skipped: list[LabDraftItemRead]


class LabUploadDetail(BaseModel):
    id: uuid.UUID
    filename: str
    status: UploadStatus
    measured_at: date | None
    parsed_at: datetime | None
    committed_at: datetime | None
    created_at: datetime
    error_message: str | None
    # Present only while awaiting review.
    draft: LabDraft | None
