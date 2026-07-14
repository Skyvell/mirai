import logging
import uuid
from datetime import UTC, date, datetime

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from mirai_api.core.enums import UploadStatus
from mirai_api.models import BiomarkerMeasurement, LabUpload
from mirai_api.repositories.biomarkers import BiomarkerRepository
from mirai_api.repositories.lab_uploads import LabUploadRepository
from mirai_api.schemas.lab_uploads import LabUploadResponse, LabUploadSummary, MeasurementOut
from mirai_api.services import storage
from mirai_api.services.lab_parsing import (
    MappedMeasurement,
    cached_catalogue,
    map_extraction,
    parse_lab_pdf,
)

logger = logging.getLogger(__name__)


class LabUploadServiceError(Exception):
    """Base for lab-upload domain errors."""


class LabUploadNotFoundError(LabUploadServiceError):
    def __init__(self, upload_id: uuid.UUID) -> None:
        super().__init__("Upload not found.")
        self.upload_id = upload_id


class LabUploadNotDeletableError(LabUploadServiceError):
    def __init__(self, upload_id: uuid.UUID) -> None:
        super().__init__("Upload is still being processed.")
        self.upload_id = upload_id


class LabParseError(LabUploadServiceError):
    def __init__(self, upload_id: uuid.UUID) -> None:
        super().__init__("Failed to parse the lab report.")
        self.upload_id = upload_id


class LabUploadService:
    """Application logic for lab uploads; owns the transaction boundary.

    Mutations take the subject user_id (whose data), never the caller: a
    future lab/admin flow authorizes the actor and passes another subject.
    """

    def __init__(
        self,
        lab_upload_repository: LabUploadRepository,
        biomarker_repository: BiomarkerRepository,
        session: Session,
    ) -> None:
        self._lab_upload_repository = lab_upload_repository
        self._biomarker_repository = biomarker_repository
        # Used for transaction control only; queries go through repositories.
        self._session = session

    def list(self, user_id: uuid.UUID) -> list[LabUploadSummary]:
        rows = self._lab_upload_repository.list_with_counts(user_id)
        return [LabUploadSummary.model_validate(r) for r in rows]

    async def submit(
        self,
        user_id: uuid.UUID,
        filename: str,
        data: bytes,
    ) -> LabUploadResponse:
        """Store the PDF, parse it, and persist the measurements. Synchronous end-to-end.

        The upload row is committed before parsing so it survives a parse
        failure (marked FAILED) for debugging and retry.
        """
        # Load the catalogue and store the PDF, both blocking.
        catalogue, prompt = await run_in_threadpool(cached_catalogue)
        upload = await run_in_threadpool(self._store_upload, user_id, filename, data)

        # Parse; on failure mark the row FAILED and abort.
        try:
            extraction = await parse_lab_pdf(data, prompt)
        except Exception as exc:
            logger.exception("Lab parse failed for upload %s", upload.id)
            await run_in_threadpool(self._mark_failed, upload)
            raise LabParseError(upload.id) from exc

        # Map against the catalogue and persist the measurements.
        mapped, skipped = map_extraction(extraction, catalogue)
        await run_in_threadpool(self._persist_results, upload, mapped, extraction.measured_at)

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

    def delete(
        self,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
        delete_measurements: bool,
    ) -> None:
        """Delete an upload; optionally its measurements, else orphan them.

        Blob first: if that fails the row survives and the delete can be
        retried, and delete_blob tolerates an already-missing blob. Deleting the
        row first would risk unrecorded orphan blobs.
        """
        # Resolve the upload scoped to the user; a miss is not-found and not-owned alike.
        upload = self._lab_upload_repository.get_for_user(user_id, upload_id)
        if upload is None:
            raise LabUploadNotFoundError(upload_id)

        # Deleting mid-parse would strand the parse's inserts on a dead FK.
        if upload.status == UploadStatus.UPLOADED:
            raise LabUploadNotDeletableError(upload_id)

        # Remove the blob, then the rows, as one transaction.
        storage.delete_blob(upload.gcs_object_name)
        if delete_measurements:
            self._lab_upload_repository.delete_measurements(upload_id)
        self._lab_upload_repository.delete(upload)
        self._session.commit()

    def _store_upload(self, user_id: uuid.UUID, filename: str, data: bytes) -> LabUpload:
        """Write the PDF to GCS, then record the upload row. Blocking."""
        upload = LabUpload(
            id=uuid.uuid7(),
            user_id=user_id,
            filename=filename,
            status=UploadStatus.UPLOADED,
        )
        storage.upload(upload.gcs_object_name, data, "application/pdf")
        self._lab_upload_repository.add(upload)
        self._session.commit()
        return upload

    def _persist_results(
        self,
        upload: LabUpload,
        mapped: list[MappedMeasurement],
        measured_at: date | None,
    ) -> None:
        """Insert measurements and mark the upload parsed. Blocking."""
        self._biomarker_repository.add_measurements(
            [
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
            ]
        )
        upload.status = UploadStatus.PARSED
        upload.parsed_at = datetime.now(UTC)
        self._session.commit()

    def _mark_failed(self, upload: LabUpload) -> None:
        """Mark a parse failure and persist it. Blocking."""
        upload.status = UploadStatus.FAILED
        self._session.commit()
