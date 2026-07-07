import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from mirai_api.core.deps import CurrentUser, DbSession
from mirai_api.models import Biomarker, BiomarkerMeasurement, LabUpload
from mirai_api.services import storage
from mirai_api.services.lab_parsing import (
    LabExtraction,
    MappedMeasurement,
    map_extraction,
    parse_lab_pdf,
)

router = APIRouter(tags=["lab-uploads"])

_MAX_BYTES = 20 * 1024 * 1024


class MeasurementOut(BaseModel):
    biomarker_slug: str
    display_name: str
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None
    measured_at: date | None


class SkippedOut(BaseModel):
    name: str
    value: str
    unit: str | None
    reason: str


class LabUploadResponse(BaseModel):
    upload_id: uuid.UUID
    filename: str
    status: str
    measured_at: date | None
    measurements: list[MeasurementOut]
    skipped: list[SkippedOut]


def _store_upload(
    session: Session, user_id: uuid.UUID, filename: str, data: bytes
) -> LabUpload:
    """Write the PDF to GCS, then record the upload row. Blocking."""
    upload = LabUpload(
        id=uuid.uuid7(), user_id=user_id, filename=filename, status="uploaded"
    )
    storage.upload_pdf(upload.gcs_object_name, data)
    session.add(upload)
    session.commit()
    return upload


def _load_catalogue(session: Session) -> list[Biomarker]:
    return list(session.scalars(select(Biomarker)))


def _persist_results(
    session: Session,
    upload: LabUpload,
    mapped: list[MappedMeasurement],
    measured_at: date | None,
) -> None:
    """Insert measurements and mark the upload parsed. Blocking."""
    session.add_all(
        BiomarkerMeasurement(
            user_id=upload.user_id,
            biomarker_id=m.biomarker.id,
            lab_upload_id=upload.id,
            value=m.value,
            unit=m.unit,
            reference_low=m.reference_low,
            reference_high=m.reference_high,
            measured_at=measured_at,
        )
        for m in mapped
    )
    upload.status = "parsed"
    upload.parsed_at = datetime.now(UTC)
    session.commit()


def _mark_failed(session: Session, upload: LabUpload) -> None:
    upload.status = "failed"
    session.commit()


@router.post("/lab-uploads", operation_id="upload_lab")
async def upload_lab(session: DbSession, user: CurrentUser, file: UploadFile = File(...)) -> LabUploadResponse:
    """Upload a lab PDF, parse it into biomarker measurements, and store both.

    Synchronous end-to-end (~10-30 s). The original PDF is kept in GCS and the
    upload row is retained even on parse failure, for debugging and retry.
    """
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty file.")
    if len(data) > _MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 20 MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "File is not a PDF."
        )

    upload = await run_in_threadpool(
        _store_upload, session, user.id, file.filename or "upload.pdf", data
    )
    catalogue = await run_in_threadpool(_load_catalogue, session)

    try:
        extraction: LabExtraction = await parse_lab_pdf(data, catalogue)
    except Exception as exc:
        await run_in_threadpool(_mark_failed, session, upload)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Failed to parse the lab report."
        ) from exc

    catalogue_by_slug = {b.slug: b for b in catalogue}
    mapped, skipped = map_extraction(extraction, catalogue_by_slug)
    await run_in_threadpool(
        _persist_results, session, upload, mapped, extraction.measured_at
    )

    return LabUploadResponse(
        upload_id=upload.id,
        filename=upload.filename,
        status=upload.status,
        measured_at=extraction.measured_at,
        measurements=[
            MeasurementOut(
                biomarker_slug=m.biomarker.slug,
                display_name=m.biomarker.display_name,
                value=m.value,
                unit=m.unit,
                reference_low=m.reference_low,
                reference_high=m.reference_high,
                measured_at=extraction.measured_at,
            )
            for m in mapped
        ],
        skipped=[
            SkippedOut(name=s.name, value=s.value, unit=s.unit, reason=s.reason)
            for s in skipped
        ],
    )
