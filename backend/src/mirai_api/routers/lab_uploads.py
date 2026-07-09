import logging

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from mirai_api.core.deps import AppSettings, CurrentUser, DbSession
from mirai_api.core.enums import UploadStatus
from mirai_api.schemas.lab_uploads import LabUploadResponse, MeasurementOut
from mirai_api.services.lab_parsing import cached_catalogue, map_extraction, parse_lab_pdf
from mirai_api.services.lab_uploads import persist_results, store_upload

logger = logging.getLogger(__name__)

router = APIRouter(tags=["lab-uploads"])

_MAX_BYTES = 20 * 1024 * 1024


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
