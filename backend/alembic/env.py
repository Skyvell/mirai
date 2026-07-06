from alembic import context

from mirai_api.core.db import get_engine
from mirai_api.models import Base

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
    """Run migrations over the app's own IAM-auth Cloud SQL engine."""
    with get_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
