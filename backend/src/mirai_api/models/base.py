from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Deterministic constraint/index names so Alembic autogenerate can diff and
# migrate them; matches SQLAlchemy's default index naming already in the schema.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(referred_table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base; Base.metadata is the schema source of truth for Alembic."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
