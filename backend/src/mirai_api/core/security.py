from functools import lru_cache

import jwt
from jwt import PyJWKClient

from mirai_api.core.config import get_settings


@lru_cache
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(get_settings().clerk_jwks_url)


def verify_clerk_token(token: str) -> dict:
    """Verify a Clerk-issued JWT against Clerk's public JWKS.

    Returns the decoded claims (``sub`` is the Clerk user id). Raises
    jwt.PyJWTError on any failure — callers translate that to a 401.
    """
    settings = get_settings()
    signing_key = _jwks_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=settings.clerk_issuer or None,
        options={"verify_aud": False, "require": ["exp", "sub"]},
    )
