from fastapi import APIRouter

from mirai_api.core.deps import CurrentUser
from mirai_api.users.schemas import MeResponse

router = APIRouter(tags=["me"])


@router.get("/me", operation_id="current_user")
def read_current_user(user: CurrentUser) -> MeResponse:
    """Return the authenticated caller's identity.

    Proves the full loop: the Bearer token is verified against Clerk's JWKS
    and the caller is resolved to (or JIT-created as) a local users row.
    """
    return MeResponse(user_id=user.id, clerk_user_id=user.clerk_user_id)
