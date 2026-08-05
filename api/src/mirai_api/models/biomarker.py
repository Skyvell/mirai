import uuid

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.models.base import Base


class Biomarker(Base):
    """A blood biomarker in the seeded, read-only reference catalogue.

    ``slug`` is the stable internal key the LLM maps to; ``loinc_code`` is the
    external key for future lab/FHIR integrations.
    """

    __tablename__ = "biomarkers"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid7,
    )
    slug: Mapped[str] = mapped_column(
        Text,
        unique=True,
    )
    display_name: Mapped[str] = mapped_column(Text)
    # LOINC identifier (e.g. "18262-6"); null where no clean single code applies.
    loinc_code: Mapped[str | None] = mapped_column(
        Text,
        index=True,
    )
    # Canonical UCUM unit — prompt guidance now, conversion target later.
    canonical_unit: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
