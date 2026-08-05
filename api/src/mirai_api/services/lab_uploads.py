import hashlib
import logging
import uuid
from datetime import UTC, date, datetime

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from mirai_api.core.enums import UploadStatus
from mirai_api.integrations import storage, tasks
from mirai_api.integrations.lab_parsing import UnmatchedMarker, parse_lab_pdf
from mirai_api.models import BiomarkerMeasurement, LabResult, LabUpload
from mirai_api.repositories.biomarkers import BiomarkerRepository
from mirai_api.repositories.lab_results import LabResultRepository
from mirai_api.repositories.lab_uploads import LabUploadRepository
from mirai_api.schemas.lab_uploads import (
    LabDraft,
    LabDraftUpdate,
    LabUploadDetail,
    LabUploadSummary,
)
from mirai_api.services.biomarkers import UnknownBiomarkersError
from mirai_api.services.lab_extraction import (
    MappedMeasurement,
    catalogue_prompt,
    map_extraction,
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


class DuplicateUploadError(LabUploadServiceError):
    def __init__(self) -> None:
        super().__init__(
            "You've already uploaded this report. Find it under Sources, "
            "or delete it there to upload it again."
        )


class LabUploadNotReviewableError(LabUploadServiceError):
    def __init__(self, upload_id: uuid.UUID) -> None:
        super().__init__("Upload is not awaiting review.")
        self.upload_id = upload_id


class DraftItemsNotFoundError(LabUploadServiceError):
    def __init__(self, ids: list[uuid.UUID]) -> None:
        super().__init__("Draft items not found.")
        self.ids = ids


class DraftNotCommittableError(LabUploadServiceError):
    def __init__(self, ids: list[uuid.UUID]) -> None:
        super().__init__("Some kept measurements are missing a value.")
        self.ids = ids


class MissingCollectionDateError(LabUploadServiceError):
    def __init__(self, upload_id: uuid.UUID) -> None:
        super().__init__("Set the collection date before committing.")
        self.upload_id = upload_id


class LabUploadService:
    """Application logic for lab uploads; owns the transaction boundary.

    Mutations take the subject user_id (whose data), never the caller: a
    future lab/admin flow authorizes the actor and passes another subject.
    """

    def __init__(
        self,
        lab_upload_repository: LabUploadRepository,
        lab_result_repository: LabResultRepository,
        biomarker_repository: BiomarkerRepository,
        session: Session,
        tasks_enabled: bool = False,
    ) -> None:
        self._lab_upload_repository = lab_upload_repository
        self._lab_result_repository = lab_result_repository
        self._biomarker_repository = biomarker_repository
        # Used for transaction control only; queries go through repositories.
        self._session = session
        # When true, parsing is dispatched to the task queue; else it runs in-request.
        self._tasks_enabled = tasks_enabled

    def list(self, user_id: uuid.UUID) -> list[LabUploadSummary]:
        rows = self._lab_upload_repository.list_with_counts(user_id)

        summaries = []
        for row in rows:
            status = _effective_status(row.status, row.created_at)
            summaries.append(LabUploadSummary.from_row(row, status=status))

        return summaries

    def get(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> LabUploadDetail:
        # Resolve the upload scoped to the user; a miss is not-found and not-owned alike.
        upload = self._lab_upload_repository.get_for_user(user_id, upload_id)
        if upload is None:
            raise LabUploadNotFoundError(upload_id)

        # A non-terminal upload that never progressed is reported as failed, not mutated.
        status = _effective_status(upload.status, upload.created_at)

        # The draft is loaded only while there is one to review.
        draft = None
        if status == UploadStatus.AWAITING_REVIEW:
            rows = self._lab_result_repository.list_for_upload(upload_id)
            draft = LabDraft.from_lab_results(rows, measured_at=upload.measured_at)

        return LabUploadDetail.from_upload(upload, status=status, draft=draft)

    async def submit(
        self,
        user_id: uuid.UUID,
        filename: str,
        data: bytes,
    ) -> LabUploadDetail:
        """Store the PDF, then parse it into a reviewable draft.

        The upload row is committed before dispatch so it survives a parse
        failure (marked failed) and so a queued worker can read its state.
        """
        # Reject a byte-identical re-upload before spending storage or an LLM call.
        content_sha256 = hashlib.sha256(data).hexdigest()
        existing = await run_in_threadpool(
            self._lab_upload_repository.find_duplicate, user_id, content_sha256
        )
        if existing is not None:
            raise DuplicateUploadError()

        # Record the upload as queued and stash the PDF in GCS.
        upload = await run_in_threadpool(
            self._store_upload, user_id, filename, data, content_sha256
        )

        # Dispatch parsing to the queue, or run it in-request where none is configured.
        if self._tasks_enabled:
            await run_in_threadpool(tasks.enqueue_parse, upload.id)
        else:
            await self.process(upload.id)

        return await run_in_threadpool(self.get, user_id, upload.id)

    async def process(self, upload_id: uuid.UUID) -> None:
        """Parse a queued upload into draft measurements. Idempotent and re-runnable.

        Claims the upload atomically; a redelivered task whose upload is no
        longer queued is a safe no-op. A parse failure is terminal (marked
        failed). Infrastructure errors reset the claim to queued and re-raise
        so the task queue retries.
        """
        # Win the claim, or bail out as a no-op on a redelivery.
        claimed = await run_in_threadpool(self._claim, upload_id)
        if not claimed:
            return

        try:
            # Load the claimed row and the catalogue, and pull the PDF back from GCS.
            upload = await run_in_threadpool(self._lab_upload_repository.get, upload_id)
            catalogue = await run_in_threadpool(self._biomarker_repository.list_biomarkers)
            prompt = catalogue_prompt(catalogue)
            data = await run_in_threadpool(storage.download, upload.gcs_object_name)

            # A parse failure is terminal for this upload, never retried.
            try:
                extraction = await parse_lab_pdf(data, prompt)
            except Exception:
                logger.exception("Lab parse failed for upload %s", upload_id)
                await run_in_threadpool(
                    self._mark_failed, upload, "Failed to parse the lab report."
                )
                return

            # Map against the catalogue and write the reviewable draft.
            mapped, unmatched = map_extraction(extraction, catalogue)
            await run_in_threadpool(
                self._write_results,
                upload,
                mapped,
                unmatched,
                extraction.measured_at,
            )
        except Exception:
            # Infrastructure failure: release the claim so the retry can re-run.
            logger.exception("Lab processing failed for upload %s", upload_id)
            await run_in_threadpool(self._reset_to_queued, upload_id)
            raise

    def update_draft(
        self,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
        payload: LabDraftUpdate,
    ) -> LabUploadDetail:
        """Apply the user's edits to a draft: keep/drop rows, correct values, map markers."""
        upload = self._require_reviewable(user_id, upload_id)

        # Fetch the targeted rows scoped to this upload; a miss is unknown or not-owned.
        ids = [item.id for item in payload.items]
        by_id = {r.id: r for r in self._lab_result_repository.get_for_upload(upload_id, ids)}
        missing = sorted(set(ids) - by_id.keys())
        if missing:
            raise DraftItemsNotFoundError(missing)

        # Resolve any catalogue slugs used to map previously unmatched markers.
        slugs = {item.biomarker_slug for item in payload.items if item.biomarker_slug is not None}
        by_slug = {b.slug: b for b in self._biomarker_repository.get_biomarkers(slugs)}
        unknown = sorted(slugs - by_slug.keys())
        if unknown:
            raise UnknownBiomarkersError(unknown)

        # Apply each item's set fields; a mapped slug clears the skip and attaches the biomarker.
        for item in payload.items:
            row = by_id[item.id]
            edits = item.model_dump(exclude_unset=True, exclude={"id", "biomarker_slug"})
            for field, value in edits.items():
                setattr(row, field, value)
            if item.biomarker_slug is not None:
                row.biomarker_id = by_slug[item.biomarker_slug].id

        upload.measured_at = payload.measured_at
        self._session.commit()
        return self.get(user_id, upload_id)

    def confirm(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> LabUploadDetail:
        """Commit the kept, mapped draft rows into the biomarker record.

        Idempotent: a repeat confirm on an already-confirmed upload is a no-op.
        Draft rows are retained as an audit trail of what was extracted.
        """
        upload = self._lab_upload_repository.get_for_user(user_id, upload_id)
        if upload is None:
            raise LabUploadNotFoundError(upload_id)
        if upload.status == UploadStatus.CONFIRMED:
            return self.get(user_id, upload_id)
        if upload.status != UploadStatus.AWAITING_REVIEW:
            raise LabUploadNotReviewableError(upload_id)

        # Measurements are time-series points; committing without a date is invalid.
        if upload.measured_at is None:
            raise MissingCollectionDateError(upload_id)

        # Only kept, mapped rows become measurements.
        rows = self._lab_result_repository.list_for_upload(upload_id)
        committable = [r for r in rows if r.included and r.biomarker_id is not None]

        # Every committed measurement needs a numeric value.
        incomplete = sorted(r.id for r in committable if r.value is None)
        if incomplete:
            raise DraftNotCommittableError(incomplete)

        # Build the measurements; unit falls back to the biomarker's canonical unit.
        measurements = [
            BiomarkerMeasurement(
                user_id=user_id,
                biomarker_id=r.biomarker_id,
                lab_upload_id=upload_id,
                value=r.value,
                unit=r.unit or r.biomarker.canonical_unit,
                reference_low=r.reference_low,
                reference_high=r.reference_high,
                measured_at=upload.measured_at,
            )
            for r in committable
        ]
        self._biomarker_repository.add_measurements(measurements)

        upload.status = UploadStatus.CONFIRMED
        upload.confirmed_at = datetime.now(UTC)
        self._session.commit()
        return self.get(user_id, upload_id)

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
        if upload.status in (UploadStatus.QUEUED, UploadStatus.PROCESSING):
            raise LabUploadNotDeletableError(upload_id)

        # Remove the blob, then the rows, as one transaction; drafts cascade.
        storage.delete_blob(upload.gcs_object_name)
        if delete_measurements:
            self._lab_upload_repository.delete_measurements(upload_id)
        self._lab_upload_repository.delete(upload)
        self._session.commit()

    def _require_reviewable(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> LabUpload:
        """Resolve an upload that must be awaiting review, for a draft mutation."""
        upload = self._lab_upload_repository.get_for_user(user_id, upload_id)
        if upload is None:
            raise LabUploadNotFoundError(upload_id)
        if upload.status != UploadStatus.AWAITING_REVIEW:
            raise LabUploadNotReviewableError(upload_id)
        return upload

    def _store_upload(
        self,
        user_id: uuid.UUID,
        filename: str,
        data: bytes,
        content_sha256: str,
    ) -> LabUpload:
        """Write the PDF to GCS, then record the queued upload row. Blocking."""
        upload = LabUpload(
            id=uuid.uuid7(),
            user_id=user_id,
            filename=filename,
            status=UploadStatus.QUEUED,
            content_sha256=content_sha256,
        )
        storage.upload(upload.gcs_object_name, data, "application/pdf")
        self._lab_upload_repository.add(upload)
        self._session.commit()
        return upload

    def _claim(self, upload_id: uuid.UUID) -> bool:
        """Commit the queued → processing transition so a redelivery sees it. Blocking."""
        claimed = self._lab_upload_repository.claim_for_processing(upload_id)
        self._session.commit()
        return claimed

    def _write_results(
        self,
        upload: LabUpload,
        mapped: list[MappedMeasurement],
        unmatched: list[UnmatchedMarker],
        measured_at: date | None,
    ) -> None:
        """Replace the upload's results with this parse and await review. Blocking."""
        # Clear any prior parse so a re-run is idempotent.
        self._lab_result_repository.delete_for_upload(upload.id)

        # Mapped measurements are kept by default; unmatched markers are carried for mapping.
        results = [
            LabResult(
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
        results += [
            LabResult(
                lab_upload_id=upload.id,
                raw_value=u.value,
                unit=u.unit,
                reference_low=u.reference_low,
                reference_high=u.reference_high,
                source_name=u.name,
                included=False,
            )
            for u in unmatched
        ]
        self._lab_result_repository.add_all(results)

        upload.status = UploadStatus.AWAITING_REVIEW
        upload.measured_at = measured_at
        upload.parsed_at = datetime.now(UTC)
        self._session.commit()

    def _mark_failed(self, upload: LabUpload, message: str) -> None:
        """Record a terminal parse failure. Blocking."""
        upload.status = UploadStatus.FAILED
        upload.error_message = message
        self._session.commit()

    def _reset_to_queued(self, upload_id: uuid.UUID) -> None:
        """Release a claim after an infrastructure failure so a retry can re-run. Blocking."""
        self._lab_upload_repository.reset_to_queued(upload_id)
        self._session.commit()


def _effective_status(status: UploadStatus, created_at: datetime) -> UploadStatus:
    """Report a long-stuck queued/processing upload as failed, without mutating it."""
    if status not in (UploadStatus.QUEUED, UploadStatus.PROCESSING):
        return status

    age = (datetime.now(UTC) - created_at).total_seconds()
    return UploadStatus.FAILED if age > _STUCK_AFTER else status
