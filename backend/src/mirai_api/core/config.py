from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables.

    Cloud Run injects the DB_* / INSTANCE_CONNECTION_NAME / CLERK_* values (see
    infra/opentofu/modules/app). Locally, an untracked backend/.env supplies them.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Cloud SQL (IAM auth — no password).
    instance_connection_name: str = ""  # project:region:instance
    db_name: str = "mirai"
    db_iam_user: str = ""  # runtime SA email, ".gserviceaccount.com" stripped

    # Clerk — JWT verification needs only the public JWKS, not the secret key.
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""  # optional; verified when set

    # CORS — the frontend origin allowed to call the API.
    frontend_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
