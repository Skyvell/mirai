import logging
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, select

from mirai_api.core.deps import AppSettings, CurrentUser, DbSession
from mirai_api.core.enums import UploadStatus
from mirai_api.models import BiomarkerMeasurement, LabUpload
from mirai_api.schemas.lab_uploads import LabUploadResponse, LabUploadSummary, MeasurementOut
from mirai_api.services.lab_parsing import cached_catalogue, map_extraction, parse_lab_pdf
from mirai_api.services.lab_uploads import delete_upload, persist_results, store_upload

logger = logging.getLogger(__name__)

router = APIRouter(tags=["lab-uploads"])

_MAX_BYTES = 20 * 1024 * 1024


@router.get("/lab-uploads", operation_id="list_lab_uploads")
def list_lab_uploads(
    session: DbSession,
    user: CurrentUser,
) -> list[LabUploadSummary]:
    """Return the caller's uploaded lab reports, newest first."""
    count_sq = (
        select(func.count())
        .select_from(BiomarkerMeasurement)
        .where(BiomarkerMeasurement.lab_upload_id == LabUpload.id)
        .scalar_subquery()
    )
    rows = session.execute(
        select(
            LabUpload.id,
            LabUpload.filename,
            LabUpload.status,
            LabUpload.parsed_at,
            LabUpload.created_at,
            count_sq.label("measurement_count"),
        )
        .where(LabUpload.user_id == user.id)
        .order_by(LabUpload.created_at.desc())
    ).all()
    return [LabUploadSummary.model_validate(r) for r in rows]


@router.delete(
    "/lab-uploads/{upload_id}",
    operation_id="delete_lab_upload",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lab_upload(
    session: DbSession,
    user: CurrentUser,
    upload_id: uuid.UUID,
    delete_measurements: bool = False,
) -> None:
    """Delete an uploaded report; optionally its measurements, else orphan them."""
    upload = session.scalar(
        select(LabUpload).where(
            LabUpload.id == upload_id,
            LabUpload.user_id == user.id,
        )
    )
    if upload is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Upload not found.",
        )
    delete_upload(
        session,
        upload,
        delete_measurements,
    )


@router.post("/lab-uploads", operation_id="upload_lab")
async def upload_lab(
    session: DbSession,
    user: CurrentUser,
    settings: AppSettings,
    file: UploadFile,
) -> LabUploadResponse:
    """Upload a lab PDF, parse it into biomarker measurements, and store both.

    Synchronous end-to-end (~10-30 s). The original PDF is kept in GCS and the
    upload row is retained even on parse failure, for debugging and retry.
    """
    allowlist = settings.upload_allowlist_ids
    if allowlist and str(user.id) not in allowlist:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Forbidden.",
        )
    if file.size is not None and file.size > _MAX_BYTES:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "File exceeds 20 MB.",
        )
    data = await file.read()
    if not data:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Empty file.",
        )
    if len(data) > _MAX_BYTES:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "File exceeds 20 MB.",
        )
    if not data.startswith(b"%PDF"):
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "File is not a PDF.",
        )

    catalogue, prompt = await run_in_threadpool(cached_catalogue)
    upload = await run_in_threadpool(
        store_upload,
        session,
        user.id,
        file.filename or "upload.pdf",
        data,
    )

    try:
        extraction = await parse_lab_pdf(data, prompt)
    except Exception as exc:
        logger.exception("Lab parse failed for upload %s", upload.id)
        upload.status = UploadStatus.FAILED
        await run_in_threadpool(session.commit)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Failed to parse the lab report.",
        ) from exc

    mapped, skipped = map_extraction(extraction, catalogue)
    await run_in_threadpool(
        persist_results,
        session,
        upload,
        mapped,
        extraction.measured_at,
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
