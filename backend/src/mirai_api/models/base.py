from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base; Base.metadata is the schema source of truth for Alembic."""
