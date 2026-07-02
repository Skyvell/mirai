from fastapi import APIRouter
from sqlalchemy import text

from mirai_api.core.deps import DbSession

router = APIRouter(tags=["health"])


@router.get("/healthz", operation_id="liveness")
def liveness() -> dict[str, str]:
    """Liveness probe — no dependencies. Used by the Cloud Run startup probe."""
    return {"status": "ok"}


@router.get("/readyz", operation_id="readiness")
def readiness(db: DbSession) -> dict[str, str]:
    """Readiness probe — confirms the Cloud SQL (IAM-auth) connection works."""
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
