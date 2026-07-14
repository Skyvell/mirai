import asyncio
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from conftest import TEST_USER_ID
from mirai_api.core.enums import UploadStatus
from mirai_api.models import Biomarker, DraftMeasurement, LabUpload
from mirai_api.services import lab_uploads, storage
from mirai_api.services.lab_parsing import (
    ExtractedMeasurement,
    LabExtraction,
    UnmatchedMarker,
)
from mirai_api.services.lab_uploads import (
    LabUploadNotDeletableError,
    LabUploadNotFoundError,
    LabUploadService,
)

GLUCOSE = Biomarker(
    id=uuid.UUID("00000000-0000-7000-8000-000000000002"),
    slug="glucose",
    display_name="Glucose",
    category="metabolic",
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

    def claim_for_processing(self, upload_id: uuid.UUID) -> bool:
        upload = self.uploads.get(upload_id)
        if upload is not None and upload.status == UploadStatus.PENDING:
            upload.status = UploadStatus.PROCESSING
            return True
        return False

    def add(self, upload: LabUpload) -> None:
        self.uploads[upload.id] = upload

    def delete(self, upload: LabUpload) -> None:
        self.deleted.append(upload)
        self.uploads.pop(upload.id, None)

    def delete_measurements(self, upload_id: uuid.UUID) -> None:
        self.deleted_measurements.append(upload_id)


class FakeDraftMeasurementRepository:
    def __init__(self, drafts: list[DraftMeasurement] | None = None) -> None:
        self.drafts = list(drafts or [])

    def add_all(self, drafts: list[DraftMeasurement]) -> None:
        for d in drafts:
            if d.id is None:
                d.id = uuid.uuid7()
        self.drafts.extend(drafts)

    def list_for_upload(self, upload_id: uuid.UUID) -> list[DraftMeasurement]:
        return [d for d in self.drafts if d.lab_upload_id == upload_id]

    def delete_for_upload(self, upload_id: uuid.UUID) -> None:
        self.drafts = [d for d in self.drafts if d.lab_upload_id != upload_id]


class FakeBiomarkerRepository:
    def __init__(self) -> None:
        self.added: list = []

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
    draft_repo: FakeDraftMeasurementRepository,
) -> LabUploadService:
    return LabUploadService(
        lab_repo,  # type: ignore[arg-type]
        draft_repo,  # type: ignore[arg-type]
        FakeBiomarkerRepository(),  # type: ignore[arg-type]
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
    draft_repo = FakeDraftMeasurementRepository()

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
    draft_repo = FakeDraftMeasurementRepository()

    asyncio.run(_service(lab_repo, draft_repo).process(upload.id))

    assert pipeline.parse_calls == 0
    assert draft_repo.drafts == []
    assert upload.status == UploadStatus.AWAITING_REVIEW


def test_process_reparse_clears_prior_drafts(pipeline: SimpleNamespace) -> None:
    upload = _upload()
    stale = DraftMeasurement(
        id=uuid.uuid7(),
        lab_upload_id=upload.id,
        biomarker_id=GLUCOSE.id,
        included=True,
    )
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftMeasurementRepository([stale])

    asyncio.run(_service(lab_repo, draft_repo).process(upload.id))

    assert stale not in draft_repo.drafts
    assert len(draft_repo.drafts) == 2


def test_process_parse_failure_marks_failed(pipeline: SimpleNamespace) -> None:
    pipeline.error = RuntimeError("model exploded")
    upload = _upload()
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftMeasurementRepository()

    asyncio.run(_service(lab_repo, draft_repo).process(upload.id))

    assert upload.status == UploadStatus.FAILED
    assert upload.error_message == "Failed to parse the lab report."
    assert draft_repo.drafts == []


def test_get_returns_split_draft_when_awaiting_review() -> None:
    upload = _upload(status=UploadStatus.AWAITING_REVIEW, measured_at=date(2026, 7, 12))
    mapped = DraftMeasurement(
        id=uuid.uuid7(),
        lab_upload_id=upload.id,
        biomarker_id=GLUCOSE.id,
        biomarker=GLUCOSE,
        value=Decimal("5.4"),
        unit="mmol/L",
        included=True,
    )
    skipped = DraftMeasurement(
        id=uuid.uuid7(),
        lab_upload_id=upload.id,
        raw_value="42",
        source_name="Exotic Marker",
        skip_reason="unmatched",
        included=False,
    )
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftMeasurementRepository([mapped, skipped])

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
    draft_repo = FakeDraftMeasurementRepository()

    detail = _service(lab_repo, draft_repo).get(TEST_USER_ID, upload.id)

    assert detail.status == UploadStatus.COMMITTED
    assert detail.draft is None


def test_get_unknown_upload_raises_not_found() -> None:
    lab_repo = FakeLabUploadRepository()
    draft_repo = FakeDraftMeasurementRepository()
    with pytest.raises(LabUploadNotFoundError):
        _service(lab_repo, draft_repo).get(TEST_USER_ID, uuid.uuid7())


def test_get_stuck_processing_reports_failed_without_mutating() -> None:
    upload = _upload(
        status=UploadStatus.PROCESSING,
        created_at=datetime(2020, 1, 1, tzinfo=UTC),
    )
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftMeasurementRepository()

    detail = _service(lab_repo, draft_repo).get(TEST_USER_ID, upload.id)

    assert detail.status == UploadStatus.FAILED
    # The stored row is untouched; only the read is reinterpreted.
    assert upload.status == UploadStatus.PROCESSING


def test_delete_committed_removes_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    upload = _upload(status=UploadStatus.COMMITTED)
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftMeasurementRepository()
    monkeypatch.setattr(storage, "delete_blob", lambda name: None)

    _service(lab_repo, draft_repo).delete(TEST_USER_ID, upload.id, delete_measurements=True)

    assert lab_repo.deleted == [upload]
    assert lab_repo.deleted_measurements == [upload.id]


def test_delete_processing_upload_is_rejected() -> None:
    upload = _upload(status=UploadStatus.PROCESSING, created_at=datetime.now(UTC))
    lab_repo = FakeLabUploadRepository([upload])
    draft_repo = FakeDraftMeasurementRepository()
    with pytest.raises(LabUploadNotDeletableError):
        _service(lab_repo, draft_repo).delete(TEST_USER_ID, upload.id, delete_measurements=False)


def test_delete_unknown_upload_raises_not_found() -> None:
    lab_repo = FakeLabUploadRepository()
    draft_repo = FakeDraftMeasurementRepository()
    with pytest.raises(LabUploadNotFoundError):
        _service(lab_repo, draft_repo).delete(TEST_USER_ID, uuid.uuid7(), delete_measurements=False)
