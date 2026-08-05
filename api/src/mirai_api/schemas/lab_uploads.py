import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict
from sqlalchemy import Row

from mirai_api.core.enums import UploadStatus
from mirai_api.models import LabResult, LabUpload
from mirai_api.schemas.biomarkers import BoundedDecimal


class LabUploadSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: UploadStatus
    parsed_at: datetime | None
    created_at: datetime
    measurement_count: int

    @classmethod
    def from_row(cls, row: Row, *, status: UploadStatus) -> LabUploadSummary:
        """Built from a listing row carrying measurement_count, not from an entity.

        The status is the service's effective status, which can differ from the
        stored one for an upload that never finished.
        """
        summary = cls.model_validate(row)
        return summary.model_copy(update={"status": status})


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
    included: bool

    @classmethod
    def from_lab_result(cls, result: LabResult) -> LabDraftItemRead:
        """Requires an eager-loaded `biomarker`; the relationship is lazy="raise"."""
        mapped = result.biomarker_id is not None
        return cls(
            id=result.id,
            biomarker_slug=result.biomarker.slug if mapped else None,
            display_name=result.biomarker.display_name if mapped else None,
            value=result.value,
            raw_value=result.raw_value,
            unit=result.unit,
            reference_low=result.reference_low,
            reference_high=result.reference_high,
            source_name=result.source_name,
            included=result.included,
        )


class LabDraft(BaseModel):
    measured_at: date | None
    items: list[LabDraftItemRead]
    skipped: list[LabDraftItemRead]

    @classmethod
    def from_lab_results(cls, results: list[LabResult], *, measured_at: date | None) -> LabDraft:
        """Unmapped rows are split out as skipped; the date comes from the upload."""
        items = [LabDraftItemRead.from_lab_result(r) for r in results if r.biomarker_id is not None]
        skipped = [LabDraftItemRead.from_lab_result(r) for r in results if r.biomarker_id is None]
        return cls(measured_at=measured_at, items=items, skipped=skipped)


class LabUploadDetail(BaseModel):
    id: uuid.UUID
    filename: str
    status: UploadStatus
    measured_at: date | None
    parsed_at: datetime | None
    confirmed_at: datetime | None
    created_at: datetime
    error_message: str | None
    # Present only while awaiting review.
    draft: LabDraft | None

    @classmethod
    def from_upload(
        cls,
        upload: LabUpload,
        *,
        status: UploadStatus,
        draft: LabDraft | None,
    ) -> LabUploadDetail:
        """Status is the service's effective status; draft is fetched separately."""
        return cls(
            id=upload.id,
            filename=upload.filename,
            status=status,
            measured_at=upload.measured_at,
            parsed_at=upload.parsed_at,
            confirmed_at=upload.confirmed_at,
            created_at=upload.created_at,
            error_message=upload.error_message,
            draft=draft,
        )


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
