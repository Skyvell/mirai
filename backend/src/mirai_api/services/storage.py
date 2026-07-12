import contextlib
from functools import lru_cache

from google.api_core.exceptions import NotFound
from google.cloud import storage

from mirai_api.core.config import get_settings


@lru_cache
def _client() -> storage.Client:
    """Cached GCS client, authenticated via ADC (the runtime SA in prod)."""
    return storage.Client(project=get_settings().gcp_project_id)


def upload(object_name: str, data: bytes, content_type: str) -> None:
    """Store bytes at object_name in the uploads bucket. Blocking; call via threadpool."""
    bucket = _client().bucket(get_settings().gcs_bucket)
    bucket.blob(object_name).upload_from_string(
        data,
        content_type=content_type,
    )


def delete_blob(object_name: str) -> None:
    """Delete object_name from the uploads bucket; already-missing objects are
    ignored so interrupted deletes stay retryable. Blocking; call via threadpool."""
    bucket = _client().bucket(get_settings().gcs_bucket)
    with contextlib.suppress(NotFound):
        bucket.blob(object_name).delete()
