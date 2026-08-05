import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    model_validator,
)

from mirai_api.models import BiomarkerMeasurement

# Bounded to the column type Numeric(12, 4) so overflow is a 422, not a 500.
BoundedDecimal = Annotated[Decimal, Field(max_digits=12, decimal_places=4)]


class BiomarkerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    display_name: str
    category: str
    canonical_unit: str


class BiomarkerMeasurementPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    measured_at: date
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None
    # Null means manual entry or a deleted source report.
    lab_upload_id: uuid.UUID | None


class BiomarkerSeriesBySlug(RootModel[dict[str, list[BiomarkerMeasurementPoint]]]):
    """Measurement time series keyed by biomarker slug; the GET /biomarker-series payload."""

    @classmethod
    def from_measurements(cls, measurements: list[BiomarkerMeasurement]) -> Self:
        """Requires an eager-loaded `biomarker`; the relationship is lazy="raise"."""
        series_by_slug: dict[str, list[BiomarkerMeasurementPoint]] = {}
        for measurement in measurements:
            slug = measurement.biomarker.slug
            if slug not in series_by_slug:
                series_by_slug[slug] = []
            series_by_slug[slug].append(BiomarkerMeasurementPoint.model_validate(measurement))

        return cls(series_by_slug)


class BiomarkerMeasurementCreate(BaseModel):
    biomarker_slug: str
    value: BoundedDecimal
    # Verbatim unit; defaults to the biomarker's canonical_unit when omitted.
    unit: str | None = None
    measured_at: date
    reference_low: BoundedDecimal | None = None
    reference_high: BoundedDecimal | None = None


class BiomarkerMeasurementUpdate(BaseModel):
    id: uuid.UUID
    value: BoundedDecimal | None = None
    unit: str | None = None
    measured_at: date | None = None
    reference_low: BoundedDecimal | None = None
    reference_high: BoundedDecimal | None = None

    @model_validator(mode="after")
    def _reject_null_for_required_columns(self) -> Self:
        # Omitted fields are left untouched; explicit null is only valid where
        # the column is nullable — derived from the model, one source of truth.
        columns = BiomarkerMeasurement.__table__.columns
        for field in self.model_fields_set:
            if getattr(self, field) is None and not columns[field].nullable:
                raise ValueError(f"{field} cannot be null.")
        return self


def _unique_ids(
    items: list[BiomarkerMeasurementUpdate],
) -> list[BiomarkerMeasurementUpdate]:
    ids = [item.id for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate measurement ids.")
    return items


BiomarkerMeasurementUpdates = Annotated[
    list[BiomarkerMeasurementUpdate],
    AfterValidator(_unique_ids),
]


class BiomarkerMeasurementRead(BiomarkerMeasurementPoint):
    biomarker_slug: str
    display_name: str

    @classmethod
    def from_measurement(cls, measurement: BiomarkerMeasurement) -> Self:
        """Requires an eager-loaded `biomarker`; the relationship is lazy="raise"."""
        # Inherited fields come from the parent, so a new column cannot be missed here.
        point = BiomarkerMeasurementPoint.model_validate(measurement)
        return cls(
            **point.model_dump(),
            biomarker_slug=measurement.biomarker.slug,
            display_name=measurement.biomarker.display_name,
        )
