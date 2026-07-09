from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables.

    Cloud Run injects these (see infra/opentofu/modules/app); locally an
    untracked backend/.env supplies them.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Cloud SQL (IAM auth — no password).
    instance_connection_name: str = ""  # project:region:instance
    db_name: str = "mirai"
    db_iam_user: str = ""  # runtime SA email, ".gserviceaccount.com" stripped

    # Clerk — JWT verification needs only the public JWKS, not the secret key.
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""  # optional; verified when set

    # CORS — comma-separated allow-list of origins permitted to call the API
    # (local dev origin now; the deployed frontend origin is added per environment).
    frontend_origins: str = "http://localhost:5173"

    # User-uploaded files (lab PDFs today), stored in GCS — keyless via ADC.
    gcs_bucket: str = ""
    gcp_project_id: str = ""

    # Claude via the Anthropic API parses lab PDFs. Key-based auth: Secret
    # Manager injects it on Cloud Run; backend/.env supplies it locally.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # LLM cost-control gate: comma-separated user UUIDs allowed to upload.
    # Empty = allow all; auth stays Clerk's job.
    upload_allowlist: str = ""

    @property
    def cors_origins(self) -> list[str]:
        """Split the comma-separated allow-list into individual origins."""
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]

    @property
    def upload_allowlist_ids(self) -> frozenset[str]:
        """Split the comma-separated allowlist; empty means allow everyone."""
        return frozenset(u.strip() for u in self.upload_allowlist.split(",") if u.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
