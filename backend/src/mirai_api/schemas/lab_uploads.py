import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict

from mirai_api.core.enums import UploadStatus
from mirai_api.schemas.biomarkers import BoundedDecimal


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


class LabDraftItemUpdate(BaseModel):
    id: uuid.UUID
    value: BoundedDecimal | None = None
    unit: str | None = None
    reference_low: BoundedDecimal | None = None
    reference_high: BoundedDecimal | None = None
    # Whether to keep this row on commit.
    included: bool | None = None
    # Maps a previously unmatched marker to a catalogue biomarker.
    biomarker_slug: str | None = None


def _unique_ids(items: list[LabDraftItemUpdate]) -> list[LabDraftItemUpdate]:
    ids = [item.id for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate draft item ids.")
    return items


class LabDraftUpdate(BaseModel):
    # The user-confirmed collection date, applied to every committed measurement.
    measured_at: date | None = None
    items: Annotated[list[LabDraftItemUpdate], AfterValidator(_unique_ids)] = []
