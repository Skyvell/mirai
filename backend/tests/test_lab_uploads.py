import uuid

from fastapi.testclient import TestClient

from mirai_api.core.config import Settings, get_settings
from mirai_api.main import app


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
