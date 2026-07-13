import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from conftest import TEST_USER_ID, FakeSession
from mirai_api.core.config import Settings, get_settings
from mirai_api.core.enums import UploadStatus
from mirai_api.main import app
from mirai_api.models import LabUpload
from mirai_api.services import storage


def _upload(client: TestClient, content: bytes) -> object:
    return client.post(
        "/lab-uploads",
        files={"file": ("report.pdf", content, "application/pdf")},
    )


def test_empty_file_is_rejected(client: TestClient) -> None:
    response = _upload(client, b"")
    assert response.status_code == 422
    assert response.json()["detail"] == "Empty file."


def test_non_pdf_is_rejected(client: TestClient) -> None:
    response = _upload(client, b"not a pdf")
    assert response.status_code == 415


def test_oversize_file_is_rejected(client: TestClient) -> None:
    response = _upload(client, b"%PDF" + b"0" * (20 * 1024 * 1024))
    assert response.status_code == 413


def test_user_outside_allowlist_is_rejected(client: TestClient) -> None:
    someone_else = str(uuid.uuid4())
    app.dependency_overrides[get_settings] = lambda: Settings(
        upload_allowlist=someone_else,
        _env_file=None,
    )
    response = _upload(client, b"%PDF fake")
    assert response.status_code == 403


def test_list_uploads_returns_summaries(
    client: TestClient,
    fake_session: FakeSession,
) -> None:
    upload_id = uuid.UUID("00000000-0000-7000-8000-000000000010")
    fake_session.rows = [
        SimpleNamespace(
            id=upload_id,
            filename="report.pdf",
            status="parsed",
            parsed_at=datetime(2026, 7, 12, 10, 0, tzinfo=UTC),
            created_at=datetime(2026, 7, 12, 9, 59, tzinfo=UTC),
            measurement_count=12,
        ),
    ]
    response = client.get("/lab-uploads")
    assert response.status_code == 200
    (summary,) = response.json()
    assert summary["id"] == str(upload_id)
    assert summary["status"] == "parsed"
    assert summary["measurement_count"] == 12


def _stored_upload(status: UploadStatus = UploadStatus.PARSED) -> LabUpload:
    return LabUpload(
        id=uuid.UUID("00000000-0000-7000-8000-000000000010"),
        user_id=TEST_USER_ID,
        filename="report.pdf",
        status=status,
    )


@pytest.fixture
def deleted_blobs(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []
    monkeypatch.setattr(
        storage,
        "delete_blob",
        calls.append,
    )
    return calls


def test_delete_missing_upload_gives_404(
    client: TestClient,
    deleted_blobs: list[str],
) -> None:
    response = client.delete(f"/lab-uploads/{uuid.uuid4()}")
    assert response.status_code == 404
    assert deleted_blobs == []


def test_delete_upload_keeps_measurements_by_default(
    client: TestClient,
    fake_session: FakeSession,
    deleted_blobs: list[str],
) -> None:
    upload = _stored_upload()
    fake_session.scalar_value = upload
    response = client.delete(f"/lab-uploads/{upload.id}")
    assert response.status_code == 204
    assert deleted_blobs == [upload.gcs_object_name]
    # No measurement DELETE: the FK's ON DELETE SET NULL detaches them.
    assert fake_session.executed == []
    assert fake_session.deleted == [upload]
    assert fake_session.commits == 1


def test_delete_upload_with_measurements_deletes_them(
    client: TestClient,
    fake_session: FakeSession,
    deleted_blobs: list[str],
) -> None:
    upload = _stored_upload()
    fake_session.scalar_value = upload
    response = client.delete(f"/lab-uploads/{upload.id}?delete_measurements=true")
    assert response.status_code == 204
    assert deleted_blobs == [upload.gcs_object_name]
    # The measurement DELETE ran before the row delete.
    assert len(fake_session.executed) == 1
    assert fake_session.deleted == [upload]


def test_delete_upload_mid_parse_is_rejected(
    client: TestClient,
    fake_session: FakeSession,
    deleted_blobs: list[str],
) -> None:
    upload = _stored_upload(status=UploadStatus.UPLOADED)
    fake_session.scalar_value = upload
    response = client.delete(f"/lab-uploads/{upload.id}")
    assert response.status_code == 409
    assert deleted_blobs == []
    assert fake_session.deleted == []
