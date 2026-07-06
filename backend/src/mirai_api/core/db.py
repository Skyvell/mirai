from collections.abc import Iterator
from functools import lru_cache

from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from mirai_api.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """SQLAlchemy engine backed by the Cloud SQL Python Connector with IAM auth.

    The same code path serves the current public-IP built-in connection and a
    future private-IP swap (change ip_type only). The connector also sidesteps
    the 108-char unix-socket path limit of the raw /cloudsql socket. Shared by
    the app (via sessions) and Alembic migrations (alembic/env.py).
    """
    settings = get_settings()
    connector = Connector(refresh_strategy="lazy")
    instance, user, db = (
        settings.instance_connection_name,
        settings.db_iam_user,
        settings.db_name,
    )

    def getconn():
        return connector.connect(
            instance,
            "pg8000",
            user=user,
            db=db,
            enable_iam_auth=True,
            ip_type=IPTypes.PUBLIC,
        )

    return create_engine("postgresql+pg8000://", creator=getconn, pool_pre_ping=True)


@lru_cache
def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    with _session_factory()() as session:
        yield session
