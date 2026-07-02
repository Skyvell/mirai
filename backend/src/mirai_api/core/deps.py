from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from mirai_api.core.db import get_session
from mirai_api.core.security import verify_clerk_token

_bearer = HTTPBearer(auto_error=True)

DbSession = Annotated[Session, Depends(get_session)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> dict:
    """Resolve the caller's Clerk claims from the Bearer token.

    Local-user upsert (Clerk ``sub`` -> own user table) is deferred until the
    user model exists; for now this returns the verified claims.
    """
    try:
        return verify_clerk_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUser = Annotated[dict, Depends(get_current_user)]
