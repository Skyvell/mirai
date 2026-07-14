from functools import lru_cache

import jwt
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
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


def verify_cloud_tasks_token(token: str, audience: str, invoker_email: str) -> None:
    """Verify a Cloud Tasks OIDC token: Google-signed, our audience, our invoker SA.

    This is the only gate on the internal parse worker (ingress stays public).
    Raises ValueError on any mismatch — callers translate that to a 403.
    """
    claims = id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        audience=audience,
    )
    if not claims.get("email_verified") or claims.get("email") != invoker_email:
        raise ValueError("Untrusted OIDC caller.")
