import uuid

from fastapi import APIRouter, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from mirai_api.core.deps import AppSettings, CurrentUser, LabUploadServiceDep
from mirai_api.schemas.lab_uploads import LabUploadResponse, LabUploadSummary
from mirai_api.services.lab_uploads import (
    LabParseError,
    LabUploadNotDeletableError,
    LabUploadNotFoundError,
    LabUploadServiceError,
)

router = APIRouter(tags=["lab-uploads"])

_MAX_BYTES = 20 * 1024 * 1024

_ERROR_STATUS = {
    LabUploadNotFoundError: status.HTTP_404_NOT_FOUND,
    LabUploadNotDeletableError: status.HTTP_409_CONFLICT,
    LabParseError: status.HTTP_502_BAD_GATEWAY,
}


def lab_upload_error_handler(request: Request, exc: LabUploadServiceError) -> JSONResponse:
    """Map domain errors to HTTP once; registered on the app in main.py."""
    return JSONResponse(
        status_code=_ERROR_STATUS[type(exc)],
        content={"detail": str(exc)},
    )


@router.get("/lab-uploads", operation_id="list_lab_uploads")
def list_lab_uploads(
    service: LabUploadServiceDep,
    user: CurrentUser,
) -> list[LabUploadSummary]:
    """Return the caller's uploaded lab reports, newest first."""
    return service.list(user.id)


@router.delete(
    "/lab-uploads/{upload_id}",
    operation_id="delete_lab_upload",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lab_upload(
    service: LabUploadServiceDep,
    user: CurrentUser,
    upload_id: uuid.UUID,
    delete_measurements: bool = False,
) -> None:
    """Delete an uploaded report; optionally its measurements, else orphan them."""
    service.delete(user.id, upload_id, delete_measurements)


@router.post("/lab-uploads", operation_id="upload_lab")
async def upload_lab(
    service: LabUploadServiceDep,
    user: CurrentUser,
    settings: AppSettings,
    file: UploadFile,
) -> LabUploadResponse:
    """Upload a lab PDF, parse it into biomarker measurements, and store both.

    Synchronous end-to-end (~10-30 s). Validates the request here; the service
    owns storage, parsing, and persistence.
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

    return await service.submit(user.id, file.filename or "upload.pdf", data)
