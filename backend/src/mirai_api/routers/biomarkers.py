from itertools import groupby

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from mirai_api.core.deps import CurrentUser, DbSession
from mirai_api.models import Biomarker, BiomarkerMeasurement
from mirai_api.schemas.biomarkers import (
    BiomarkerSeries,
    CatalogBiomarker,
    MeasurementCreate,
    MeasurementCreated,
    MeasurementPoint,
)

router = APIRouter(tags=["biomarkers"])


@router.get("/biomarkers/catalog", operation_id="list_biomarker_catalog")
def list_biomarker_catalog(
    session: DbSession,
    user: CurrentUser,
) -> list[CatalogBiomarker]:
    """Return the full seeded biomarker catalogue, for manual-entry pickers."""
    rows = session.execute(
        select(
            Biomarker.slug,
            Biomarker.display_name,
            Biomarker.category,
            Biomarker.canonical_unit,
        ).order_by(
            Biomarker.category,
            Biomarker.display_name,
        )
    ).all()
    return [CatalogBiomarker.model_validate(r) for r in rows]


@router.post(
    "/biomarkers/{slug}/measurements",
    operation_id="create_measurement",
    status_code=status.HTTP_201_CREATED,
)
def create_measurement(
    session: DbSession,
    user: CurrentUser,
    slug: str,
    payload: MeasurementCreate,
) -> MeasurementCreated:
    """Record a manually entered measurement against a catalogue biomarker."""
    biomarker = session.scalar(select(Biomarker).where(Biomarker.slug == slug))
    if biomarker is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Unknown biomarker.",
        )
    unit = payload.unit or biomarker.canonical_unit
    session.add(
        BiomarkerMeasurement(
            user_id=user.id,
            biomarker_id=biomarker.id,
            lab_upload_id=None,
            value=payload.value,
            unit=unit,
            measured_at=payload.measured_at,
        )
    )
    session.commit()
    return MeasurementCreated(
        display_name=biomarker.display_name,
        value=payload.value,
        unit=unit,
    )


@router.get("/biomarkers", operation_id="list_biomarkers")
def list_biomarkers(session: DbSession, user: CurrentUser) -> list[BiomarkerSeries]:
    """Return each biomarker the caller has measurements for, with its time series.

    Values, units, and reference ranges are verbatim from the lab report;
    canonical_unit is catalogue context. Series are sorted by measurement date
    ascending, so the latest value is the last element.
    """
    # The ORDER BY is the response contract: the first three keys set the list
    # order and make each biomarker's rows contiguous for groupby; the last two
    # set the within-series order.
    rows = session.execute(
        select(
            Biomarker.slug,
            Biomarker.display_name,
            Biomarker.category,
            Biomarker.canonical_unit,
            BiomarkerMeasurement.measured_at,
            BiomarkerMeasurement.value,
            BiomarkerMeasurement.unit,
            BiomarkerMeasurement.reference_low,
            BiomarkerMeasurement.reference_high,
        )
        .join(Biomarker, BiomarkerMeasurement.biomarker_id == Biomarker.id)
        .where(BiomarkerMeasurement.user_id == user.id)
        .order_by(
            Biomarker.category,
            Biomarker.display_name,
            Biomarker.slug,
            BiomarkerMeasurement.measured_at.nulls_last(),
            BiomarkerMeasurement.created_at,
        )
    ).all()

    return [
        BiomarkerSeries(
            slug=slug,
            display_name=display_name,
            category=category,
            canonical_unit=canonical_unit,
            measurements=[
                MeasurementPoint(
                    measured_at=r.measured_at,
                    value=r.value,
                    unit=r.unit,
                    reference_low=r.reference_low,
                    reference_high=r.reference_high,
                )
                for r in points
            ],
        )
        for (slug, display_name, category, canonical_unit), points in groupby(
            rows, key=lambda r: (r.slug, r.display_name, r.category, r.canonical_unit)
        )
    ]
