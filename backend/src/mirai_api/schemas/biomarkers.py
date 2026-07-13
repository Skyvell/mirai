import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

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
    measured_at: date | None
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None
    # Null means manual entry or a deleted source report.
    lab_upload_id: uuid.UUID | None


class BiomarkerSeries(BiomarkerRead):
    measurements: list[BiomarkerMeasurementPoint]


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
