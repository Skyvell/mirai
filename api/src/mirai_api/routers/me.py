from fastapi import APIRouter

from mirai_api.core.deps import CurrentUser, UserServiceDep
from mirai_api.models import User
from mirai_api.schemas.me import MeResponse, MeUpdate

router = APIRouter(tags=["me"])


def _to_me_response(user: User) -> MeResponse:
    return MeResponse(
        user_id=user.id,
        clerk_user_id=user.clerk_user_id,
        sex=user.sex,
        date_of_birth=user.date_of_birth,
    )


@router.get("/me", operation_id="current_user")
def read_current_user(user: CurrentUser) -> MeResponse:
    """Return the authenticated caller's identity and profile.

    Proves the full loop: the Bearer token is verified against Clerk's JWKS
    and the caller is resolved to (or JIT-created as) a local users row.
    """
    return _to_me_response(user)


@router.patch("/me", operation_id="update_current_user")
def update_current_user(
    service: UserServiceDep,
    user: CurrentUser,
    payload: MeUpdate,
) -> MeResponse:
    """Set the caller's profile: biological sex and date of birth."""
    updated = service.update_profile(user, payload)
    return _to_me_response(updated)
