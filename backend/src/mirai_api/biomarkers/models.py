import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.core.db import Base


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


class BiomarkerMeasurement(Base):
    """A single biomarker value parsed from a lab report, stored verbatim."""

    __tablename__ = "biomarker_measurements"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid7,
    )
    # Denormalized (also reachable via the upload) for per-user time-series queries.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    biomarker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biomarkers.id", ondelete="RESTRICT"),
    )
    lab_upload_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_uploads.id", ondelete="CASCADE"),
        index=True,
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    unit: Mapped[str] = mapped_column(Text)
    reference_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    reference_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    measured_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_biomarker_measurements_user_series",
            "user_id",
            "biomarker_id",
            "measured_at",
        ),
    )
