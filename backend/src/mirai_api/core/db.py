from collections.abc import Generator
from functools import lru_cache

from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from mirai_api.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create the shared SQLAlchemy engine for Cloud SQL IAM auth."""
    # Load the Cloud SQL connection contract from environment-backed settings.
    settings = get_settings()
    connector = Connector(refresh_strategy="lazy")

    # SQLAlchemy calls this whenever its pool needs a new DB <-> API connection.
    def create_connection():
        return connector.connect(
            settings.instance_connection_name,
            "pg8000",
            user=settings.db_iam_user,
            db=settings.db_name,
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC,
        )

    # Let SQLAlchemy manage pooling while Cloud SQL owns connection creation.
    return create_engine(
        "postgresql+pg8000://",
        creator=create_connection,
        pool_pre_ping=True,
    )


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session]:
    factory = _session_factory()
    with factory() as session:
        yield session


def warm_engine() -> None:
    """Open a startup connection and fail fast if Cloud SQL is unreachable."""
    engine = get_engine()
    ping = text("SELECT 1")
    with engine.connect() as connection:
        connection.execute(ping)
