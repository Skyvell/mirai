from fastapi import APIRouter

from mirai_api.core.deps import CurrentUser

router = APIRouter(tags=["me"])


@router.get("/me", operation_id="current_user")
def read_current_user(user: CurrentUser) -> dict[str, str]:
    """Return the authenticated caller's Clerk identity.

    Proves the auth loop end to end: the Bearer token is verified against
    Clerk's JWKS by the CurrentUser dependency, and ``sub`` is the Clerk user id.
    """
    return {"user_id": user["sub"]}
