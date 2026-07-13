from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from mirai_api.core.config import Settings, get_settings
from mirai_api.core.db import get_session
from mirai_api.core.security import verify_clerk_token
from mirai_api.models import User
from mirai_api.repositories.biomarkers import BiomarkerRepository
from mirai_api.services.biomarkers import BiomarkerService

_bearer = HTTPBearer(auto_error=True)

DbSession = Annotated[Session, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_biomarker_service(session: DbSession) -> BiomarkerService:
    return BiomarkerService(BiomarkerRepository(session))


BiomarkerServiceDep = Annotated[BiomarkerService, Depends(get_biomarker_service)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    session: DbSession,
) -> User:
    """Resolve the caller to a local User row, creating it just-in-time.

    The Bearer token is verified against Clerk's JWKS; ``sub`` is the Clerk
    user id. On the first authenticated request there is no local row yet, so
    one is inserted — ON CONFLICT DO NOTHING keeps concurrent first requests
    race-safe, and the re-select returns whichever insert won.
    """
    try:
        claims = verify_clerk_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Token verified; map the Clerk identity to a local row, creating it on first sight.
    clerk_user_id = claims["sub"]
    lookup = select(User).where(User.clerk_user_id == clerk_user_id)
    user = session.scalar(lookup)
    if user is None:
        session.execute(
            insert(User)
            .values(clerk_user_id=clerk_user_id)
            .on_conflict_do_nothing(index_elements=["clerk_user_id"])
        )
        session.commit()
        user = session.scalar(lookup)
    if user is None:
        raise RuntimeError("User row missing after upsert.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
