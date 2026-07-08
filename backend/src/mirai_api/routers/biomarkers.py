from datetime import date
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from mirai_api.core.deps import CurrentUser, DbSession
from mirai_api.models import Biomarker, BiomarkerMeasurement

router = APIRouter(tags=["biomarkers"])


class MeasurementPoint(BaseModel):
    measured_at: date | None
    value: Decimal
    unit: str
    reference_low: Decimal | None
    reference_high: Decimal | None


class BiomarkerSeries(BaseModel):
    slug: str
    display_name: str
    category: str
    canonical_unit: str
    measurements: list[MeasurementPoint]


@router.get("/biomarkers", operation_id="list_biomarkers")
def list_biomarkers(session: DbSession, user: CurrentUser) -> list[BiomarkerSeries]:
    """Return each biomarker the caller has measurements for, with its time series.

    Values, units, and reference ranges are verbatim from the lab report;
    canonical_unit is catalogue context. Series are sorted by measurement date
    ascending, so the latest value is the last element.
    """
    rows = session.execute(
        select(BiomarkerMeasurement, Biomarker)
        .join(Biomarker, BiomarkerMeasurement.biomarker_id == Biomarker.id)
        .where(BiomarkerMeasurement.user_id == user.id)
        .order_by(
            Biomarker.category,
            Biomarker.display_name,
            BiomarkerMeasurement.measured_at.asc().nulls_last(),
            BiomarkerMeasurement.created_at,
        )
    ).all()

    series: dict[str, BiomarkerSeries] = {}
    for measurement, biomarker in rows:
        entry = series.get(biomarker.slug)
        if entry is None:
            entry = series[biomarker.slug] = BiomarkerSeries(
                slug=biomarker.slug,
                display_name=biomarker.display_name,
                category=biomarker.category,
                canonical_unit=biomarker.canonical_unit,
                measurements=[],
            )
        entry.measurements.append(
            MeasurementPoint(
                measured_at=measurement.measured_at,
                value=measurement.value,
                unit=measurement.unit,
                reference_low=measurement.reference_low,
                reference_high=measurement.reference_high,
            )
        )
    return list(series.values())
