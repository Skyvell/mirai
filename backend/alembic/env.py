import logging
import os

from alembic import context
from sqlalchemy import create_engine

from mirai_api.core.db import get_engine
from mirai_api.models import Base

# Surface Alembic's revision log in the migration job's output (the ini-less
# [tool.alembic] setup carries no logging config); root stays at WARNING so
# SQLAlchemy doesn't echo every statement.
logging.basicConfig(format="%(levelname)s [%(name)s] %(message)s")
logging.getLogger("alembic").setLevel(logging.INFO)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit migration SQL without a database connection (--sql mode)."""
    context.configure(
        dialect_name="postgresql",
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations over the app's own IAM-auth Cloud SQL engine.

    DATABASE_URL overrides the engine for local scratch databases (e.g. a
    throwaway Postgres when authoring or verifying migrations).
    """
    url = os.environ.get("DATABASE_URL")
    engine = create_engine(url) if url else get_engine()
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
