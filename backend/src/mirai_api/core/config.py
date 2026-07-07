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

    # CORS — comma-separated allow-list of origins permitted to call the API
    # (local dev origin now; the deployed frontend origin is added per environment).
    frontend_origins: str = "http://localhost:5173"

    # User-uploaded files (lab PDFs today) and the Vertex AI Claude client that
    # parses them. All keyless via ADC — no secrets. vertex_region is a Vertex
    # multi-region (eu/global), distinct from the GCP compute region.
    gcs_bucket: str = ""
    gcp_project_id: str = ""
    vertex_region: str = "eu"

    @property
    def cors_origins(self) -> list[str]:
        """Split the comma-separated allow-list into individual origins."""
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
