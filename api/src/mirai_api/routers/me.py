from fastapi import APIRouter

from mirai_api.core.deps import CurrentUser, UserServiceDep
from mirai_api.schemas.me import MeResponse, MeUpdate

router = APIRouter(tags=["me"])


@router.get("/me", operation_id="current_user")
def read_current_user(service: UserServiceDep, user: CurrentUser) -> MeResponse:
    """Return the authenticated caller's identity and profile.

    Proves the full loop: the Bearer token is verified against Clerk's JWKS
    and the caller is resolved to (or JIT-created as) a local users row.
    """
    return service.get_profile(user)


@router.patch("/me", operation_id="update_current_user")
def update_current_user(
    service: UserServiceDep,
    user: CurrentUser,
    payload: MeUpdate,
) -> MeResponse:
    """Set the caller's profile: biological sex and date of birth."""
    return service.update_profile(user, payload)
