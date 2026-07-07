from functools import lru_cache

from google.cloud import storage

from mirai_api.core.config import get_settings


@lru_cache
def _client() -> storage.Client:
    """Cached GCS client, authenticated via ADC (the runtime SA in prod)."""
    return storage.Client(project=get_settings().gcp_project_id)


def upload_pdf(object_name: str, data: bytes) -> None:
    """Store a PDF at object_name in the uploads bucket. Blocking; call via threadpool."""
    bucket = _client().bucket(get_settings().gcs_bucket)
    bucket.blob(object_name).upload_from_string(data, content_type="application/pdf")
