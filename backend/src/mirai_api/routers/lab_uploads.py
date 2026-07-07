import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.orm import Session

from mirai_api.core.deps import CurrentUser, DbSession
from mirai_api.models import BiomarkerMeasurement, LabUpload
from mirai_api.services import storage
from mirai_api.services.lab_parsing import (
    MappedMeasurement,
    SkippedMarker,
    cached_catalogue,
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


class LabUploadResponse(BaseModel):
    upload_id: uuid.UUID
    measured_at: date | None
    measurements: list[MeasurementOut]
    skipped: list[SkippedMarker]


def _store_upload(
    session: Session, user_id: uuid.UUID, filename: str, data: bytes
) -> LabUpload:
    """Write the PDF to GCS, then record the upload row. Blocking."""
    upload = LabUpload(
        id=uuid.uuid7(), user_id=user_id, filename=filename, status="uploaded"
    )
    storage.upload(upload.gcs_object_name, data, "application/pdf")
    session.add(upload)
    session.commit()
    return upload


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
            value=m.measurement.value,
            unit=m.measurement.unit,
            reference_low=m.measurement.reference_low,
            reference_high=m.measurement.reference_high,
            measured_at=measured_at,
        )
        for m in mapped
    )
    upload.status = "parsed"
    upload.parsed_at = datetime.now(UTC)
    session.commit()


@router.post("/lab-uploads", operation_id="upload_lab")
async def upload_lab(session: DbSession, user: CurrentUser, file: UploadFile) -> LabUploadResponse:
    """Upload a lab PDF, parse it into biomarker measurements, and store both.

    Synchronous end-to-end (~10-30 s). The original PDF is kept in GCS and the
    upload row is retained even on parse failure, for debugging and retry.
    """
    if str(user.id) != "019f38f2-880d-7463-b5e4-9e976369aa08":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden.")
    if file.size is not None and file.size > _MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 20 MB.")
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty file.")
    if len(data) > _MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 20 MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "File is not a PDF.")

    catalogue, prompt = cached_catalogue()
    upload = await run_in_threadpool(
        _store_upload, session, user.id, file.filename or "upload.pdf", data
    )

    try:
        extraction = await parse_lab_pdf(data, prompt)
    except Exception as exc:
        upload.status = "failed"
        await run_in_threadpool(session.commit)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Failed to parse the lab report."
        ) from exc

    mapped, skipped = map_extraction(extraction, catalogue)
    await run_in_threadpool(
        _persist_results, session, upload, mapped, extraction.measured_at
    )

    return LabUploadResponse(
        upload_id=upload.id,
        measured_at=extraction.measured_at,
        measurements=[
            MeasurementOut(
                biomarker_slug=m.biomarker.slug,
                display_name=m.biomarker.display_name,
                value=m.measurement.value,
                unit=m.measurement.unit,
                reference_low=m.measurement.reference_low,
                reference_high=m.measurement.reference_high,
            )
            for m in mapped
        ],
        skipped=skipped,
    )
