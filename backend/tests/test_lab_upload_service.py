import asyncio
import hashlib
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from conftest import TEST_USER_ID
from mirai_api.core.enums import UploadStatus
from mirai_api.models import Biomarker, DraftBiomarkerMeasurement, LabUpload
from mirai_api.schemas.lab_uploads import LabDraftItemUpdate, LabDraftUpdate
from mirai_api.services import lab_uploads, storage
from mirai_api.services.biomarkers import UnknownBiomarkersError
from mirai_api.services.lab_parsing import (
    ExtractedMeasurement,
    LabExtraction,
    UnmatchedMarker,
)
from mirai_api.services.lab_uploads import (
    DraftItemsNotFoundError,
    DraftNotCommittableError,
    DuplicateUploadError,
    LabUploadNotDeletableError,
    LabUploadNotFoundError,
    LabUploadNotReviewableError,
    LabUploadService,
)

GLUCOSE = Biomarker(
    id=uuid.UUID("00000000-0000-7000-8000-000000000002"),
    slug="glucose",
    display_name="Glucose",
    category="metabolic",
    canonical_unit="mmol/L",
)

LDL = Biomarker(
    id=uuid.UUID("00000000-0000-7000-8000-000000000003"),
    slug="ldl_cholesterol",
    display_name="LDL Cholesterol",
    category="lipids",
    canonical_unit="mmol/L",
)

CATALOGUE = [GLUCOSE]

EXTRACTION = LabExtraction(
    measured_at=date(2026, 7, 12),
    measurements=[
        ExtractedMeasurement(
            biomarker_slug="glucose",
            value=Decimal("5.4"),
            unit="mmol/L",
            reference_low=None,
            reference_high=Decimal("6.0"),
        )
    ],
    unmatched=[UnmatchedMarker(name="Exotic Marker", value="42", unit="ng/mL")],
)


class FakeSession:
    """Session double: counts commits, holds no state."""

    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


class FakeLabUploadRepository:
    def __init__(self, uploads: list[LabUpload] | None = None) -> None:
        self.uploads = {u.id: u for u in (uploads or [])}
        self.deleted: list[LabUpload] = []
        self.deleted_measurements: list[uuid.UUID] = []

    def get_for_user(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> LabUpload | None:
        upload = self.uploads.get(upload_id)
        return upload if upload is not None and upload.user_id == user_id else None

    def get(self, upload_id: uuid.UUID) -> LabUpload | None:
        return self.uploads.get(upload_id)

    def find_duplicate(self, user_id: uuid.UUID, content_sha256: str) -> LabUpload | None:
        matches = [
            u
            for u in self.uploads.values()
            if u.user_id == user_id
            and u.content_sha256 == content_sha256
            and u.status != UploadStatus.FAILED
        ]
        return max(matches, key=lambda u: u.created_at, default=None)

    def list_with_counts(self, user_id: uuid.UUID) -> list[SimpleNamespace]:
        rows = [
            SimpleNamespace(
                id=u.id,
                filename=u.filename,
                status=u.status,
                parsed_at=u.parsed_at,
                created_at=u.created_at,
                measurement_count=0,
            )
            for u in self.uploads.values()
            if u.user_id == user_id
        ]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)

    def claim_for_processing(self, upload_id: uuid.UUID) -> bool:
        upload = self.uploads.get(upload_id)
        if upload is not None and upload.status == UploadStatus.PENDING:
            upload.status = UploadStatus.PROCESSING
            return True
        return False

    def reset_to_pending(self, upload_id: uuid.UUID) -> None:
        upload = self.uploads.get(upload_id)
        if upload is not None and upload.status == UploadStatus.PROCESSING:
            upload.status = UploadStatus.PENDING

    def add(self, upload: LabUpload) -> None:
        # Mimic the DB server_default that stamps created_at on insert.
        if upload.created_at is None:
            upload.created_at = datetime.now(UTC)
        self.uploads[upload.id] = upload

    def delete(self, upload: LabUpload) -> None:
        self.deleted.append(upload)
        self.uploads.pop(upload.id, None)

    def delete_measurements(self, upload_id: uuid.UUID) -> None:
        self.deleted_measurements.append(upload_id)


class FakeDraftBiomarkerMeasurementRepository:
    def __init__(self, drafts: list[DraftBiomarkerMeasurement] | None = None) -> None:
        self.drafts = list(drafts or [])

    def add_all(self, drafts: list[DraftBiomarkerMeasurement]) -> None:
        for d in drafts:
            if d.id is None:
                d.id = uuid.uuid7()
        self.drafts.extend(drafts)

    def list_for_upload(self, upload_id: uuid.UUID) -> list[DraftBiomarkerMeasurement]:
        return [d for d in self.drafts if d.lab_upload_id == upload_id]

    def get_for_upload(
        self,
        upload_id: uuid.UUID,
        ids: list[uuid.UUID],
    ) -> list[DraftBiomarkerMeasurement]:
        wanted = set(ids)
        return [d for d in self.drafts if d.lab_upload_id == upload_id and d.id in wanted]

    def delete_for_upload(self, upload_id: uuid.UUID) -> None:
        self.drafts = [d for d in self.drafts if d.lab_upload_id != upload_id]


class FakeBiomarkerRepository:
    def __init__(self, biomarkers: list[Biomarker] | None = None) -> None:
        self.biomarkers = biomarkers or []
        self.added: list = []

    def get_biomarkers(self, slugs: list[str]) -> list[Biomarker]:
        wanted = set(slugs)
        return [b for b in self.biomarkers if b.slug in wanted]

    def add_measurements(self, measurements: list) -> None:
        self.added.extend(measurements)


def _upload(**overrides: object) -> LabUpload:
    fields: dict = {
        "id": uuid.uuid7(),
        "user_id": TEST_USER_ID,
        "filename": "report.pdf",
        "status": UploadStatus.PENDING,
        "created_at": datetime.now(UTC),
    }
    fields.update(overrides)
    return LabUpload(**fields)


def _service(
    lab_repo: FakeLabUploadRepository,
    draft_repo: FakeDraftBiomarkerMeasurementRepository,
    biomarker_repo: FakeBiomarkerRepository | None = None,
) -> LabUploadService:
    return LabUploadService(
        lab_repo,  # type: ignore[arg-type]
        draft_repo,  # type: ignore[arg-type]
        biomarker_repo or FakeBiomarkerRepository(),  # type: ignore[arg-type]
        FakeSession(),  # type: ignore[arg-type]
    )


@pytest.fixture
def pipeline(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch the blocking parse pipeline; expose parse call count and failure toggle."""
    holder = SimpleNamespace(parse_calls=0, error=None)

    monkeypatch.setattr(lab_uploads, "cached_catalogue", lambda: (CATALOGUE, "prompt"))
    monkeypatch.setattr(storage, "upload", lambda *a, **k: None)
    monkeypatch.setattr(storage, "download", lambda name: b"%PDF")
    monkeypatch.setattr(storage, "delete_blob", lambda name: None)

    async def fake_parse(data: bytes, prompt: str) -> LabExtraction:
        holder.parse_calls += 1
        if holder.error is not None:
            raise holder.error
        return EXTRACTION

    monkeypatch.setattr(lab_uploads, "parse_lab_pdf", fake_parse)
    return holder


def test_process_writes_drafts_and_awaits_review(pipeline: SimpleNamespace) -> None:
    upload = _upload()
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    asyncio.run(_service(lab_repo, draft_repo).process(upload.id))

    assert upload.status == UploadStatus.AWAITING_REVIEW
    assert upload.measured_at == date(2026, 7, 12)
    assert upload.parsed_at is not None
    # One mapped (kept) and one unmatched (carried, not kept).
    mapped = [d for d in draft_repo.drafts if d.biomarker_id is not None]
    skipped = [d for d in draft_repo.drafts if d.biomarker_id is None]
    assert len(mapped) == 1
    assert mapped[0].included is True
    assert mapped[0].value == Decimal("5.4")
    assert len(skipped) == 1
    assert skipped[0].included is False
    assert skipped[0].skip_reason == "unmatched"
    assert skipped[0].source_name == "Exotic Marker"


def test_process_is_idempotent_on_redelivery(pipeline: SimpleNamespace) -> None:
    # Already past the claimable state: a redelivered task must be a no-op.
    upload = _upload(status=UploadStatus.AWAITING_REVIEW)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    asyncio.run(_service(lab_repo, draft_repo).process(upload.id))

    assert pipeline.parse_calls == 0
    assert draft_repo.drafts == []
    assert upload.status == UploadStatus.AWAITING_REVIEW


def test_process_reparse_clears_prior_drafts(pipeline: SimpleNamespace) -> None:
    upload = _upload()
    stale = DraftBiomarkerMeasurement(
        id=uuid.uuid7(),
        lab_upload_id=upload.id,
        biomarker_id=GLUCOSE.id,
        included=True,
    )
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository([stale])

    asyncio.run(_service(lab_repo, draft_repo).process(upload.id))

    assert stale not in draft_repo.drafts
    assert len(draft_repo.drafts) == 2


def test_process_infra_failure_resets_to_pending(
    pipeline: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A GCS/DB failure (not a parse failure) is retryable: release the claim and re-raise.
    def boom(name: str) -> bytes:
        raise RuntimeError("gcs unavailable")

    monkeypatch.setattr(storage, "download", boom)
    upload = _upload()
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    with pytest.raises(RuntimeError):
        asyncio.run(_service(lab_repo, draft_repo).process(upload.id))

    assert upload.status == UploadStatus.PENDING
    assert draft_repo.drafts == []


def test_process_parse_failure_marks_failed(pipeline: SimpleNamespace) -> None:
    pipeline.error = RuntimeError("model exploded")
    upload = _upload()
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    asyncio.run(_service(lab_repo, draft_repo).process(upload.id))

    assert upload.status == UploadStatus.FAILED
    assert upload.error_message == "Failed to parse the lab report."
    assert draft_repo.drafts == []


def test_get_returns_split_draft_when_awaiting_review() -> None:
    upload = _upload(status=UploadStatus.AWAITING_REVIEW, measured_at=date(2026, 7, 12))
    mapped = DraftBiomarkerMeasurement(
        id=uuid.uuid7(),
        lab_upload_id=upload.id,
        biomarker_id=GLUCOSE.id,
        biomarker=GLUCOSE,
        value=Decimal("5.4"),
        unit="mmol/L",
        included=True,
    )
    skipped = DraftBiomarkerMeasurement(
        id=uuid.uuid7(),
        lab_upload_id=upload.id,
        raw_value="42",
        source_name="Exotic Marker",
        skip_reason="unmatched",
        included=False,
    )
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository([mapped, skipped])

    detail = _service(lab_repo, draft_repo).get(TEST_USER_ID, upload.id)

    assert detail.status == UploadStatus.AWAITING_REVIEW
    assert detail.draft is not None
    assert detail.draft.measured_at == date(2026, 7, 12)
    (item,) = detail.draft.items
    assert item.biomarker_slug == "glucose"
    assert item.value == Decimal("5.4")
    (skip,) = detail.draft.skipped
    assert skip.biomarker_slug is None
    assert skip.source_name == "Exotic Marker"


def test_get_committed_upload_has_no_draft() -> None:
    upload = _upload(status=UploadStatus.COMMITTED)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    detail = _service(lab_repo, draft_repo).get(TEST_USER_ID, upload.id)

    assert detail.status == UploadStatus.COMMITTED
    assert detail.draft is None


def test_get_unknown_upload_raises_not_found() -> None:
    lab_repo = FakeLabUploadRepository()
    draft_repo = FakeDraftBiomarkerMeasurementRepository()
    with pytest.raises(LabUploadNotFoundError):
        _service(lab_repo, draft_repo).get(TEST_USER_ID, uuid.uuid7())


def test_get_stuck_processing_reports_failed_without_mutating() -> None:
    upload = _upload(
        status=UploadStatus.PROCESSING,
        created_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    detail = _service(lab_repo, draft_repo).get(TEST_USER_ID, upload.id)

    assert detail.status == UploadStatus.FAILED
    # The stored row is untouched; only the read is reinterpreted.
    assert upload.status == UploadStatus.PROCESSING


def test_list_reports_stuck_upload_as_failed() -> None:
    stuck = _upload(
        status=UploadStatus.PENDING,
        created_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    recent = _upload(status=UploadStatus.PROCESSING, created_at=datetime.now(UTC))
    committed = _upload(status=UploadStatus.COMMITTED, created_at=datetime.now(UTC))
    lab_repo = FakeLabUploadRepository([stuck, recent, committed])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    by_id = {s.id: s.status for s in _service(lab_repo, draft_repo).list(TEST_USER_ID)}

    # The stuck row reads as failed; a recent one and terminal states pass through.
    assert by_id[stuck.id] == UploadStatus.FAILED
    assert by_id[recent.id] == UploadStatus.PROCESSING
    assert by_id[committed.id] == UploadStatus.COMMITTED
    # The stored row is untouched; only the read is reinterpreted.
    assert stuck.status == UploadStatus.PENDING


def test_delete_committed_removes_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    upload = _upload(status=UploadStatus.COMMITTED)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()
    monkeypatch.setattr(storage, "delete_blob", lambda name: None)

    _service(lab_repo, draft_repo).delete(TEST_USER_ID, upload.id, delete_measurements=True)

    assert lab_repo.deleted == [upload]
    assert lab_repo.deleted_measurements == [upload.id]


def test_delete_processing_upload_is_rejected() -> None:
    upload = _upload(status=UploadStatus.PROCESSING, created_at=datetime.now(UTC))
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()
    with pytest.raises(LabUploadNotDeletableError):
        _service(lab_repo, draft_repo).delete(TEST_USER_ID, upload.id, delete_measurements=False)


def test_delete_unknown_upload_raises_not_found() -> None:
    lab_repo = FakeLabUploadRepository()
    draft_repo = FakeDraftBiomarkerMeasurementRepository()
    with pytest.raises(LabUploadNotFoundError):
        _service(lab_repo, draft_repo).delete(TEST_USER_ID, uuid.uuid7(), delete_measurements=False)


def _mapped_draft(upload_id: uuid.UUID, **overrides: object) -> DraftBiomarkerMeasurement:
    fields: dict = {
        "id": uuid.uuid7(),
        "lab_upload_id": upload_id,
        "biomarker_id": GLUCOSE.id,
        "biomarker": GLUCOSE,
        "value": Decimal("5.4"),
        "unit": "mmol/L",
        "included": True,
    }
    fields.update(overrides)
    return DraftBiomarkerMeasurement(**fields)


def _skipped_draft(upload_id: uuid.UUID, **overrides: object) -> DraftBiomarkerMeasurement:
    fields: dict = {
        "id": uuid.uuid7(),
        "lab_upload_id": upload_id,
        "raw_value": "42",
        "source_name": "Exotic Marker",
        "skip_reason": "unmatched",
        "included": False,
    }
    fields.update(overrides)
    return DraftBiomarkerMeasurement(**fields)


def test_update_draft_applies_edits_and_maps_skipped() -> None:
    upload = _upload(status=UploadStatus.AWAITING_REVIEW)
    mapped = _mapped_draft(upload.id)
    skipped = _skipped_draft(upload.id)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository([mapped, skipped])
    biomarker_repo = FakeBiomarkerRepository([GLUCOSE, LDL])

    payload = LabDraftUpdate(
        measured_at=date(2026, 7, 13),
        items=[
            LabDraftItemUpdate(id=mapped.id, value=Decimal("6.0")),
            LabDraftItemUpdate(
                id=skipped.id,
                biomarker_slug="ldl_cholesterol",
                value=Decimal("1.5"),
                included=True,
            ),
        ],
    )
    detail = _service(lab_repo, draft_repo, biomarker_repo).update_draft(
        TEST_USER_ID, upload.id, payload
    )

    assert mapped.value == Decimal("6.0")
    assert skipped.biomarker_id == LDL.id
    assert skipped.skip_reason is None
    assert skipped.included is True
    assert upload.measured_at == date(2026, 7, 13)
    # Both rows are now mapped, so nothing is left in the skipped section.
    assert detail.draft is not None
    assert len(detail.draft.items) == 2
    assert detail.draft.skipped == []


def test_update_draft_unknown_item_raises_not_found() -> None:
    upload = _upload(status=UploadStatus.AWAITING_REVIEW)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()
    payload = LabDraftUpdate(items=[LabDraftItemUpdate(id=uuid.uuid7())])
    with pytest.raises(DraftItemsNotFoundError):
        _service(lab_repo, draft_repo).update_draft(TEST_USER_ID, upload.id, payload)


def test_update_draft_unknown_slug_raises() -> None:
    upload = _upload(status=UploadStatus.AWAITING_REVIEW)
    skipped = _skipped_draft(upload.id)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository([skipped])
    biomarker_repo = FakeBiomarkerRepository([GLUCOSE])
    payload = LabDraftUpdate(items=[LabDraftItemUpdate(id=skipped.id, biomarker_slug="nope")])
    with pytest.raises(UnknownBiomarkersError):
        _service(lab_repo, draft_repo, biomarker_repo).update_draft(
            TEST_USER_ID, upload.id, payload
        )


def test_update_draft_wrong_state_is_rejected() -> None:
    upload = _upload(status=UploadStatus.COMMITTED)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()
    with pytest.raises(LabUploadNotReviewableError):
        _service(lab_repo, draft_repo).update_draft(TEST_USER_ID, upload.id, LabDraftUpdate())


def test_confirm_commits_only_kept_mapped_rows() -> None:
    upload = _upload(status=UploadStatus.AWAITING_REVIEW, measured_at=date(2026, 7, 12))
    kept = _mapped_draft(upload.id, unit=None)  # unit falls back to canonical.
    dropped = _mapped_draft(upload.id, included=False)
    unmapped = _skipped_draft(upload.id, included=True)  # kept but never mapped.
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository([kept, dropped, unmapped])
    biomarker_repo = FakeBiomarkerRepository([GLUCOSE])

    detail = _service(lab_repo, draft_repo, biomarker_repo).confirm(TEST_USER_ID, upload.id)

    assert upload.status == UploadStatus.COMMITTED
    assert upload.committed_at is not None
    assert detail.status == UploadStatus.COMMITTED
    (measurement,) = biomarker_repo.added
    assert measurement.biomarker_id == GLUCOSE.id
    assert measurement.unit == "mmol/L"
    assert measurement.measured_at == date(2026, 7, 12)


def test_confirm_is_idempotent_when_committed() -> None:
    upload = _upload(status=UploadStatus.COMMITTED)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()
    biomarker_repo = FakeBiomarkerRepository([GLUCOSE])

    _service(lab_repo, draft_repo, biomarker_repo).confirm(TEST_USER_ID, upload.id)

    assert biomarker_repo.added == []


def test_confirm_rejects_kept_row_without_value() -> None:
    upload = _upload(status=UploadStatus.AWAITING_REVIEW)
    incomplete = _mapped_draft(upload.id, value=None)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository([incomplete])
    biomarker_repo = FakeBiomarkerRepository([GLUCOSE])
    with pytest.raises(DraftNotCommittableError):
        _service(lab_repo, draft_repo, biomarker_repo).confirm(TEST_USER_ID, upload.id)


def test_confirm_wrong_state_is_rejected() -> None:
    upload = _upload(status=UploadStatus.PENDING)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()
    with pytest.raises(LabUploadNotReviewableError):
        _service(lab_repo, draft_repo).confirm(TEST_USER_ID, upload.id)


_PDF = b"%PDF-lab-report"
_PDF_SHA256 = hashlib.sha256(_PDF).hexdigest()


def test_submit_rejects_byte_identical_reupload(pipeline: SimpleNamespace) -> None:
    existing = _upload(status=UploadStatus.COMMITTED, content_sha256=_PDF_SHA256)
    lab_repo = FakeLabUploadRepository([existing])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    with pytest.raises(DuplicateUploadError):
        asyncio.run(_service(lab_repo, draft_repo).submit(TEST_USER_ID, "again.pdf", _PDF))

    # Nothing was stored or parsed.
    assert len(lab_repo.uploads) == 1
    assert pipeline.parse_calls == 0


def test_submit_stores_hash_and_parses_when_new(pipeline: SimpleNamespace) -> None:
    lab_repo = FakeLabUploadRepository()
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    detail = asyncio.run(
        _service(lab_repo, draft_repo, FakeBiomarkerRepository(CATALOGUE)).submit(
            TEST_USER_ID, "report.pdf", _PDF
        )
    )

    stored = lab_repo.uploads[detail.id]
    assert stored.content_sha256 == _PDF_SHA256
    assert detail.status == UploadStatus.AWAITING_REVIEW


def test_submit_allows_reupload_of_differing_bytes(pipeline: SimpleNamespace) -> None:
    existing = _upload(status=UploadStatus.COMMITTED, content_sha256="deadbeef")
    lab_repo = FakeLabUploadRepository([existing])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    detail = asyncio.run(
        _service(lab_repo, draft_repo, FakeBiomarkerRepository(CATALOGUE)).submit(
            TEST_USER_ID, "report.pdf", _PDF
        )
    )

    assert detail.status == UploadStatus.AWAITING_REVIEW
    assert len(lab_repo.uploads) == 2


def test_submit_allows_reupload_after_prior_failed(pipeline: SimpleNamespace) -> None:
    # A failed prior upload of the same file must not block a retry.
    failed = _upload(status=UploadStatus.FAILED, content_sha256=_PDF_SHA256)
    lab_repo = FakeLabUploadRepository([failed])
    draft_repo = FakeDraftBiomarkerMeasurementRepository()

    detail = asyncio.run(
        _service(lab_repo, draft_repo, FakeBiomarkerRepository(CATALOGUE)).submit(
            TEST_USER_ID, "report.pdf", _PDF
        )
    )

    assert detail.status == UploadStatus.AWAITING_REVIEW
    assert len(lab_repo.uploads) == 2
