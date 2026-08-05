import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mirai_api.core.enums import IntervalType, Sex
from mirai_api.models.base import Base
from mirai_api.models.biomarker import Biomarker


class BiomarkerInterval(Base):
    """A canonical, platform-owned low/high band for a biomarker.

    One row per (biomarker, type, sex, age band). NULL on any stratification
    axis means "no constraint": a null sex applies to any sex, a null age bound
    is unbounded. Age is canonical days, half-open [min, max). Bounds are in the
    biomarker's canonical_unit; the read endpoint projects that unit rather than
    storing a copy that could drift.
    """

    __tablename__ = "biomarker_intervals"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid7,
    )
    biomarker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("biomarkers.id", ondelete="RESTRICT"),
    )

    # values_callable stores the lowercase values, not the member names.
    type: Mapped[IntervalType] = mapped_column(
        Enum(
            IntervalType,
            name="biomarker_interval_type",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        server_default=IntervalType.REFERENCE.value,
    )

    # Null applies to any sex.
    sex: Mapped[Sex | None] = mapped_column(
        Enum(
            Sex,
            name="sex",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda e: [m.value for m in e],
        ),
    )

    # Half-open [min, max) in canonical days; null is unbounded, 0 is from birth.
    age_min_days: Mapped[int | None] = mapped_column(Integer)
    age_max_days: Mapped[int | None] = mapped_column(Integer)

    # Either bound may be null for a one-sided interval.
    interval_low: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    interval_high: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))

    source: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # lazy="raise" forbids accidental lazy loads; the repository eager-loads it.
    biomarker: Mapped[Biomarker] = relationship(lazy="raise")

    __table_args__ = (
        UniqueConstraint(
            "biomarker_id",
            "type",
            "sex",
            "age_min_days",
            "age_max_days",
            name="uq_biomarker_intervals_stratum",
        ),
        CheckConstraint(
            "interval_low IS NOT NULL OR interval_high IS NOT NULL",
            name="one_sided_or_bounded",
        ),
        CheckConstraint(
            "interval_low IS NULL OR interval_high IS NULL OR interval_low <= interval_high",
            name="low_not_above_high",
        ),
        CheckConstraint(
            "age_min_days IS NULL OR age_max_days IS NULL OR age_min_days < age_max_days",
            name="age_min_below_max",
        ),
    )
