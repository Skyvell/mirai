import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from mirai_api.core.deps import CurrentUser

router = APIRouter(tags=["me"])


class MeResponse(BaseModel):
    user_id: uuid.UUID
    clerk_user_id: str


@router.get("/me", operation_id="current_user")
def read_current_user(user: CurrentUser) -> MeResponse:
    """Return the authenticated caller's identity.

    Proves the full loop: the Bearer token is verified against Clerk's JWKS
    and the caller is resolved to (or JIT-created as) a local users row.
    """
    return MeResponse(user_id=user.id, clerk_user_id=user.clerk_user_id)
