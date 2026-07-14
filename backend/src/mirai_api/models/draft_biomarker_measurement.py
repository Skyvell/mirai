import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mirai_api.models.base import Base
from mirai_api.models.biomarker import Biomarker


class DraftBiomarkerMeasurement(Base):
    """An extracted lab value awaiting the user's review, before it is committed.

    Keeps unreviewed LLM output structurally out of the biomarker record. A row
    with a biomarker_id is a mapped measurement; a null biomarker_id is a marker
    the parser could not match (skip_reason set), carried so the user can map it.
    """

    __tablename__ = "draft_biomarker_measurements"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid7,
    )
    lab_upload_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_uploads.id", ondelete="CASCADE"),
        index=True,
    )
    biomarker_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("biomarkers.id", ondelete="RESTRICT"),
    )
    # lazy="raise" forbids accidental lazy loads; repository queries eager-load it.
    biomarker: Mapped[Biomarker | None] = relationship(lazy="raise")
    value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    # Verbatim printed value, kept for unmatched markers whose value may be non-numeric.
    raw_value: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(Text)
    reference_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    reference_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    # Parser's original analyte name, kept for unmatched markers.
    source_name: Mapped[str | None] = mapped_column(Text)
    # Why the marker was not mapped: unmatched | unknown_slug | null when mapped.
    skip_reason: Mapped[str | None] = mapped_column(Text)
    # Whether the user keeps this row on commit; mapped rows default true, skipped false.
    included: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
