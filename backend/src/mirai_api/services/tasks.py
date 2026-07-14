import json
import uuid
from functools import lru_cache

from google.cloud import tasks_v2

from mirai_api.core.config import get_settings


@lru_cache
def _client() -> tasks_v2.CloudTasksClient:
    """Cached Cloud Tasks client, authenticated via ADC (the runtime SA in prod)."""
    return tasks_v2.CloudTasksClient()


def enqueue_parse(upload_id: uuid.UUID) -> None:
    """Enqueue a parse task for an upload. Blocking; call via threadpool.

    The task POSTs to the internal worker with an OIDC token the worker
    verifies; the body carries only the id, so the worker re-reads state and
    the PDF from their sources of truth.
    """
    settings = get_settings()
    client = _client()

    parent = client.queue_path(
        settings.gcp_project_id,
        settings.tasks_location,
        settings.tasks_queue,
    )
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{settings.worker_base_url}/internal/lab-uploads/{upload_id}/parse",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"upload_id": str(upload_id)}).encode(),
            "oidc_token": {
                "service_account_email": settings.task_invoker_sa,
                "audience": settings.worker_base_url,
            },
        }
    }
    client.create_task(parent=parent, task=task)
