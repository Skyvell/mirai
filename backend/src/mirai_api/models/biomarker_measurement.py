import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from mirai_api.models.base import Base


class BiomarkerMeasurement(Base):
    """A single biomarker value parsed from a lab report.

    ``value``/``unit`` are stored verbatim as reported — the immutable source
    of truth, never mutated by a future unit conversion. ``user_id`` is
    denormalized (also reachable via the upload) for fast per-user time-series
    queries.
    """

    __tablename__ = "biomarker_measurements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    biomarker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biomarkers.id", ondelete="RESTRICT")
    )
    lab_upload_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_uploads.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    unit: Mapped[str] = mapped_column(Text)
    reference_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    reference_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    measured_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_biomarker_measurements_user_series",
            "user_id",
            "biomarker_id",
            "measured_at",
        ),
    )
