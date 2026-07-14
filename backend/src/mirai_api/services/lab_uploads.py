import logging
import uuid
from datetime import UTC, date, datetime

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from mirai_api.core.enums import UploadStatus
from mirai_api.models import DraftMeasurement, LabUpload
from mirai_api.repositories.biomarkers import BiomarkerRepository
from mirai_api.repositories.draft_measurements import DraftMeasurementRepository
from mirai_api.repositories.lab_uploads import LabUploadRepository
from mirai_api.schemas.lab_uploads import (
    LabDraft,
    LabDraftItemRead,
    LabUploadDetail,
    LabUploadSummary,
)
from mirai_api.services import storage
from mirai_api.services.lab_parsing import (
    MappedMeasurement,
    SkippedMarker,
    cached_catalogue,
    map_extraction,
    parse_lab_pdf,
)

logger = logging.getLogger(__name__)

# Uploads stuck in a non-terminal state past this are surfaced as failed.
_STUCK_AFTER = 10 * 60


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


class LabUploadService:
    """Application logic for lab uploads; owns the transaction boundary.

    Mutations take the subject user_id (whose data), never the caller: a
    future lab/admin flow authorizes the actor and passes another subject.
    """

    def __init__(
        self,
        lab_upload_repository: LabUploadRepository,
        draft_measurement_repository: DraftMeasurementRepository,
        biomarker_repository: BiomarkerRepository,
        session: Session,
    ) -> None:
        self._lab_upload_repository = lab_upload_repository
        self._draft_measurement_repository = draft_measurement_repository
        self._biomarker_repository = biomarker_repository
        # Used for transaction control only; queries go through repositories.
        self._session = session

    def list(self, user_id: uuid.UUID) -> list[LabUploadSummary]:
        rows = self._lab_upload_repository.list_with_counts(user_id)
        return [LabUploadSummary.model_validate(r) for r in rows]

    def get(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> LabUploadDetail:
        # Resolve the upload scoped to the user; a miss is not-found and not-owned alike.
        upload = self._lab_upload_repository.get_for_user(user_id, upload_id)
        if upload is None:
            raise LabUploadNotFoundError(upload_id)

        # A non-terminal upload that never progressed is reported as failed, not mutated.
        status = _effective_status(upload)

        # The draft is loaded only while there is one to review.
        draft = None
        if status == UploadStatus.AWAITING_REVIEW:
            rows = self._draft_measurement_repository.list_for_upload(upload_id)
            draft = _to_draft(upload.measured_at, rows)

        return _to_detail(upload, status, draft)

    async def submit(
        self,
        user_id: uuid.UUID,
        filename: str,
        data: bytes,
    ) -> LabUploadDetail:
        """Store the PDF, then parse it into a reviewable draft.

        Transport is synchronous for now: parsing runs in-request. The upload
        row is committed first so it survives a parse failure (marked failed).
        """
        # Record the upload as pending and stash the PDF in GCS.
        upload = await run_in_threadpool(self._store_upload, user_id, filename, data)

        # Parse in-process; a later stage moves this onto a task queue.
        await self.process(upload.id)

        return await run_in_threadpool(self.get, user_id, upload.id)

    async def process(self, upload_id: uuid.UUID) -> None:
        """Parse a pending upload into draft measurements. Idempotent and re-runnable.

        Claims the upload atomically; a redelivered task whose upload is no
        longer pending is a safe no-op. Parse failure marks the upload failed
        rather than raising — the state is surfaced to the user on read.
        """
        # Win the claim, or bail out as a no-op on a redelivery.
        claimed = await run_in_threadpool(self._claim, upload_id)
        if not claimed:
            return

        # Load the claimed row and the catalogue, and pull the PDF back from GCS.
        upload = await run_in_threadpool(self._lab_upload_repository.get, upload_id)
        catalogue, prompt = await run_in_threadpool(cached_catalogue)
        data = await run_in_threadpool(storage.download, upload.gcs_object_name)

        # Parse; a failure is terminal for this upload.
        try:
            extraction = await parse_lab_pdf(data, prompt)
        except Exception:
            logger.exception("Lab parse failed for upload %s", upload_id)
            await run_in_threadpool(self._mark_failed, upload, "Failed to parse the lab report.")
            return

        # Map against the catalogue and write the reviewable draft.
        mapped, skipped = map_extraction(extraction, catalogue)
        await run_in_threadpool(
            self._write_drafts,
            upload,
            mapped,
            skipped,
            extraction.measured_at,
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

        # Deleting mid-parse would strand the worker's inserts on a dead FK.
        if upload.status in (UploadStatus.PENDING, UploadStatus.PROCESSING):
            raise LabUploadNotDeletableError(upload_id)

        # Remove the blob, then the rows, as one transaction; drafts cascade.
        storage.delete_blob(upload.gcs_object_name)
        if delete_measurements:
            self._lab_upload_repository.delete_measurements(upload_id)
        self._lab_upload_repository.delete(upload)
        self._session.commit()

    def _store_upload(self, user_id: uuid.UUID, filename: str, data: bytes) -> LabUpload:
        """Write the PDF to GCS, then record the pending upload row. Blocking."""
        upload = LabUpload(
            id=uuid.uuid7(),
            user_id=user_id,
            filename=filename,
            status=UploadStatus.PENDING,
        )
        storage.upload(upload.gcs_object_name, data, "application/pdf")
        self._lab_upload_repository.add(upload)
        self._session.commit()
        return upload

    def _claim(self, upload_id: uuid.UUID) -> bool:
        """Commit the pending → processing transition so a redelivery sees it. Blocking."""
        claimed = self._lab_upload_repository.claim_for_processing(upload_id)
        self._session.commit()
        return claimed

    def _write_drafts(
        self,
        upload: LabUpload,
        mapped: list[MappedMeasurement],
        skipped: list[SkippedMarker],
        measured_at: date | None,
    ) -> None:
        """Replace the upload's draft with this parse and await review. Blocking."""
        # Clear any prior parse so a re-run is idempotent.
        self._draft_measurement_repository.delete_for_upload(upload.id)

        # Mapped measurements are kept by default; unmatched markers are carried for mapping.
        drafts = [
            DraftMeasurement(
                lab_upload_id=upload.id,
                biomarker_id=m.biomarker.id,
                value=m.measurement.value,
                unit=m.measurement.unit,
                reference_low=m.measurement.reference_low,
                reference_high=m.measurement.reference_high,
                included=True,
            )
            for m in mapped
        ]
        drafts += [
            DraftMeasurement(
                lab_upload_id=upload.id,
                raw_value=s.value,
                unit=s.unit,
                source_name=s.name,
                skip_reason=s.reason,
                included=False,
            )
            for s in skipped
        ]
        self._draft_measurement_repository.add_all(drafts)

        upload.status = UploadStatus.AWAITING_REVIEW
        upload.measured_at = measured_at
        upload.parsed_at = datetime.now(UTC)
        self._session.commit()

    def _mark_failed(self, upload: LabUpload, message: str) -> None:
        """Record a terminal parse failure. Blocking."""
        upload.status = UploadStatus.FAILED
        upload.error_message = message
        self._session.commit()


def _effective_status(upload: LabUpload) -> UploadStatus:
    """Report a long-stuck pending/processing upload as failed, without mutating it."""
    if upload.status not in (UploadStatus.PENDING, UploadStatus.PROCESSING):
        return upload.status

    age = (datetime.now(UTC) - upload.created_at).total_seconds()
    return UploadStatus.FAILED if age > _STUCK_AFTER else upload.status


def _to_detail(
    upload: LabUpload,
    status: UploadStatus,
    draft: LabDraft | None,
) -> LabUploadDetail:
    return LabUploadDetail(
        id=upload.id,
        filename=upload.filename,
        status=status,
        measured_at=upload.measured_at,
        parsed_at=upload.parsed_at,
        committed_at=upload.committed_at,
        created_at=upload.created_at,
        error_message=upload.error_message,
        draft=draft,
    )


def _to_draft(measured_at: date | None, rows: list[DraftMeasurement]) -> LabDraft:
    items = [_to_draft_item(r) for r in rows if r.biomarker_id is not None]
    skipped = [_to_draft_item(r) for r in rows if r.biomarker_id is None]
    return LabDraft(measured_at=measured_at, items=items, skipped=skipped)


def _to_draft_item(row: DraftMeasurement) -> LabDraftItemRead:
    return LabDraftItemRead(
        id=row.id,
        biomarker_slug=row.biomarker.slug if row.biomarker_id else None,
        display_name=row.biomarker.display_name if row.biomarker_id else None,
        value=row.value,
        raw_value=row.raw_value,
        unit=row.unit,
        reference_low=row.reference_low,
        reference_high=row.reference_high,
        source_name=row.source_name,
        skip_reason=row.skip_reason,
        included=row.included,
    )
