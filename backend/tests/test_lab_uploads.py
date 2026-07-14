import uuid
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from conftest import TEST_USER_ID
from mirai_api.core.config import Settings, get_settings
from mirai_api.core.deps import get_lab_upload_service
from mirai_api.core.enums import UploadStatus
from mirai_api.main import app
from mirai_api.schemas.lab_uploads import (
    LabDraft,
    LabDraftItemRead,
    LabUploadDetail,
    LabUploadSummary,
)
from mirai_api.services.lab_uploads import (
    DraftItemsNotFoundError,
    DraftNotCommittableError,
    LabUploadNotDeletableError,
    LabUploadNotFoundError,
    LabUploadNotReviewableError,
)

UPLOAD_ID = uuid.UUID("00000000-0000-7000-8000-000000000010")

SUMMARY = LabUploadSummary(
    id=UPLOAD_ID,
    filename="report.pdf",
    status=UploadStatus.COMMITTED,
    parsed_at=datetime(2026, 7, 12, 10, 0, tzinfo=UTC),
    created_at=datetime(2026, 7, 12, 9, 59, tzinfo=UTC),
    measurement_count=12,
)

DETAIL = LabUploadDetail(
    id=UPLOAD_ID,
    filename="report.pdf",
    status=UploadStatus.AWAITING_REVIEW,
    measured_at=date(2026, 7, 12),
    parsed_at=datetime(2026, 7, 12, 10, 0, tzinfo=UTC),
    committed_at=None,
    created_at=datetime(2026, 7, 12, 9, 59, tzinfo=UTC),
    error_message=None,
    draft=LabDraft(
        measured_at=date(2026, 7, 12),
        items=[
            LabDraftItemRead(
                id=uuid.UUID("00000000-0000-7000-8000-000000000021"),
                biomarker_slug="glucose",
                display_name="Glucose",
                value="5.4",
                raw_value=None,
                unit="mmol/L",
                reference_low=None,
                reference_high=None,
                source_name=None,
                skip_reason=None,
                included=True,
            )
        ],
        skipped=[],
    ),
)


class StubLabUploadService:
    """Service stub: canned returns out, calls recorded, optional error raised."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.summaries: list[LabUploadSummary] = []
        self.detail: LabUploadDetail = DETAIL
        self.error: Exception | None = None

    def _record(self, *call: object) -> None:
        self.calls.append(call)
        if self.error is not None:
            raise self.error

    def list(self, user_id: uuid.UUID) -> list[LabUploadSummary]:
        self._record("list", user_id)
        return self.summaries

    def get(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> LabUploadDetail:
        self._record("get", user_id, upload_id)
        return self.detail

    async def submit(self, user_id: uuid.UUID, filename: str, data: bytes) -> LabUploadDetail:
        self._record("submit", user_id, filename, data)
        return self.detail

    def update_draft(
        self, user_id: uuid.UUID, upload_id: uuid.UUID, payload: object
    ) -> LabUploadDetail:
        self._record("update_draft", user_id, upload_id, payload)
        return self.detail

    def confirm(self, user_id: uuid.UUID, upload_id: uuid.UUID) -> LabUploadDetail:
        self._record("confirm", user_id, upload_id)
        return self.detail

    def delete(
        self,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
        delete_measurements: bool,
    ) -> None:
        self._record("delete", user_id, upload_id, delete_measurements)


@pytest.fixture
def stub_service(client: TestClient) -> StubLabUploadService:
    # The client fixture clears all dependency overrides at teardown.
    stub = StubLabUploadService()
    app.dependency_overrides[get_lab_upload_service] = lambda: stub
    return stub


def _upload(client: TestClient, content: bytes):
    return client.post(
        "/lab-uploads",
        files={"file": ("report.pdf", content, "application/pdf")},
    )


def test_empty_file_is_rejected(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    response = _upload(client, b"")
    assert response.status_code == 422
    assert response.json()["detail"] == "Empty file."
    assert stub_service.calls == []


def test_non_pdf_is_rejected(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    response = _upload(client, b"not a pdf")
    assert response.status_code == 415
    assert stub_service.calls == []


def test_oversize_file_is_rejected(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    response = _upload(client, b"%PDF" + b"0" * (20 * 1024 * 1024))
    assert response.status_code == 413
    assert stub_service.calls == []


def test_user_outside_allowlist_is_rejected(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    someone_else = str(uuid.uuid4())
    app.dependency_overrides[get_settings] = lambda: Settings(
        upload_allowlist=someone_else,
        _env_file=None,
    )
    response = _upload(client, b"%PDF fake")
    assert response.status_code == 403
    assert stub_service.calls == []


def test_upload_accepts_and_delegates(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    response = _upload(client, b"%PDF real-ish")
    assert response.status_code == 202
    assert response.headers["location"] == f"/lab-uploads/{UPLOAD_ID}"
    body = response.json()
    assert body["id"] == str(UPLOAD_ID)
    assert body["status"] == "awaiting_review"
    (name, user_id, filename, data) = stub_service.calls[0]
    assert name == "submit"
    assert user_id == TEST_USER_ID
    assert filename == "report.pdf"
    assert data == b"%PDF real-ish"


def test_list_uploads_delegates(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    stub_service.summaries = [SUMMARY]
    response = client.get("/lab-uploads")
    assert response.status_code == 200
    (summary,) = response.json()
    assert summary["id"] == str(UPLOAD_ID)
    assert summary["status"] == "committed"
    assert summary["measurement_count"] == 12
    assert stub_service.calls == [("list", TEST_USER_ID)]


def test_get_upload_returns_detail_with_draft(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    response = client.get(f"/lab-uploads/{UPLOAD_ID}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "awaiting_review"
    (item,) = body["draft"]["items"]
    assert item["biomarker_slug"] == "glucose"
    assert item["value"] == "5.4"
    assert body["draft"]["skipped"] == []
    assert stub_service.calls == [("get", TEST_USER_ID, UPLOAD_ID)]


def test_get_missing_upload_gives_404(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    stub_service.error = LabUploadNotFoundError(UPLOAD_ID)
    response = client.get(f"/lab-uploads/{UPLOAD_ID}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Upload not found."


def test_delete_delegates_with_flag(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    response = client.delete(f"/lab-uploads/{UPLOAD_ID}?delete_measurements=true")
    assert response.status_code == 204
    assert stub_service.calls == [("delete", TEST_USER_ID, UPLOAD_ID, True)]


def test_delete_missing_upload_gives_404(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    stub_service.error = LabUploadNotFoundError(UPLOAD_ID)
    response = client.delete(f"/lab-uploads/{UPLOAD_ID}")
    assert response.status_code == 404


def test_delete_upload_mid_parse_is_rejected(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    stub_service.error = LabUploadNotDeletableError(UPLOAD_ID)
    response = client.delete(f"/lab-uploads/{UPLOAD_ID}")
    assert response.status_code == 409


def test_update_draft_delegates(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    item_id = "00000000-0000-7000-8000-000000000021"
    response = client.patch(
        f"/lab-uploads/{UPLOAD_ID}/draft",
        json={
            "measured_at": "2026-07-13",
            "items": [{"id": item_id, "value": "6.0", "included": True}],
        },
    )
    assert response.status_code == 200
    (name, user_id, upload_id, payload) = stub_service.calls[0]
    assert name == "update_draft"
    assert user_id == TEST_USER_ID
    assert upload_id == UPLOAD_ID
    assert payload.measured_at == date(2026, 7, 13)
    assert str(payload.items[0].id) == item_id


def test_update_draft_duplicate_ids_give_422(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    item_id = "00000000-0000-7000-8000-000000000021"
    response = client.patch(
        f"/lab-uploads/{UPLOAD_ID}/draft",
        json={"items": [{"id": item_id}, {"id": item_id}]},
    )
    assert response.status_code == 422
    assert stub_service.calls == []


def test_update_draft_unknown_item_gives_404(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    stub_service.error = DraftItemsNotFoundError([UPLOAD_ID])
    response = client.patch(f"/lab-uploads/{UPLOAD_ID}/draft", json={"items": []})
    assert response.status_code == 404


def test_confirm_delegates(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    response = client.post(f"/lab-uploads/{UPLOAD_ID}/confirm")
    assert response.status_code == 200
    assert stub_service.calls == [("confirm", TEST_USER_ID, UPLOAD_ID)]


def test_confirm_wrong_state_gives_409(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    stub_service.error = LabUploadNotReviewableError(UPLOAD_ID)
    response = client.post(f"/lab-uploads/{UPLOAD_ID}/confirm")
    assert response.status_code == 409


def test_confirm_incomplete_draft_gives_422(
    client: TestClient,
    stub_service: StubLabUploadService,
) -> None:
    stub_service.error = DraftNotCommittableError([UPLOAD_ID])
    response = client.post(f"/lab-uploads/{UPLOAD_ID}/confirm")
    assert response.status_code == 422
