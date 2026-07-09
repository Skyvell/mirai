from functools import lru_cache

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
