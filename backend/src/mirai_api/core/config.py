from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_csv_env(value: str) -> list[str]:
    """Parse a comma-separated env var into stripped, non-empty values."""
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Cloud SQL, authenticated via IAM.
    instance_connection_name: str = ""
    db_name: str = "mirai"
    db_iam_user: str = ""

    # Clerk JWT verification.
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""

    # Browser origins allowed to call the API.
    frontend_origins: str = "http://localhost:5173"

    # User-uploaded files in GCS.
    gcs_bucket: str = ""
    gcp_project_id: str = ""

    # Lab PDF parsing via Anthropic.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # Empty means all authenticated users may upload.
    upload_allowlist: str = ""

    # Async lab parsing via Cloud Tasks. When disabled, parsing runs in-request.
    tasks_enabled: bool = False
    tasks_queue: str = ""
    tasks_location: str = ""
    # Service account Cloud Tasks mints OIDC tokens as; also the accepted worker caller.
    task_invoker_sa: str = ""
    # Base URL of this service, the parse worker's target and OIDC audience.
    worker_base_url: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return _parse_csv_env(self.frontend_origins)

    @property
    def upload_allowlist_ids(self) -> frozenset[str]:
        return frozenset(_parse_csv_env(self.upload_allowlist))


@lru_cache
def get_settings() -> Settings:
    return Settings()
