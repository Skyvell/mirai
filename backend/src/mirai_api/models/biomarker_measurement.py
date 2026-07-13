import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mirai_api.models.base import Base
from mirai_api.models.biomarker import Biomarker


class BiomarkerMeasurement(Base):
    """A single biomarker value, stored verbatim.

    Sourced from a parsed lab report or entered manually; lab_upload_id is
    null for manual entries and for measurements whose report was deleted.
    """

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
    # SET NULL keeps measurements when their report is deleted; deleting them
    # too is an explicit choice made in the service layer.
    lab_upload_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lab_uploads.id", ondelete="SET NULL"),
        index=True,
    )
    # lazy="raise" forbids accidental lazy loads; repository queries eager-load it.
    biomarker: Mapped[Biomarker] = relationship(lazy="raise")
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
