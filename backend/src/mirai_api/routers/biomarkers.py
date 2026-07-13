import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Query, Request, status
from fastapi.responses import JSONResponse

from mirai_api.core.deps import BiomarkerServiceDep, CurrentUser
from mirai_api.schemas.biomarkers import (
    BiomarkerMeasurementCreate,
    BiomarkerMeasurementRead,
    BiomarkerMeasurementUpdates,
    BiomarkerRead,
    BiomarkerSeries,
)
from mirai_api.services.biomarkers import (
    BiomarkerServiceError,
    MeasurementsNotFoundError,
    UnknownBiomarkersError,
)

router = APIRouter(tags=["biomarkers"])

_ERROR_STATUS = {
    UnknownBiomarkersError: status.HTTP_404_NOT_FOUND,
    MeasurementsNotFoundError: status.HTTP_404_NOT_FOUND,
}


def biomarker_error_handler(request: Request, exc: BiomarkerServiceError) -> JSONResponse:
    """Map domain errors to HTTP once; registered on the app in main.py."""
    return JSONResponse(
        status_code=_ERROR_STATUS[type(exc)],
        content={"detail": str(exc)},
    )


@router.get("/biomarkers", operation_id="list_biomarkers")
def list_biomarkers(
    service: BiomarkerServiceDep,
    user: CurrentUser,
) -> list[BiomarkerRead]:
    """Return the full seeded biomarker catalogue, for manual-entry pickers."""
    return service.list_biomarkers()


@router.get("/biomarker-series", operation_id="list_biomarker_series")
def list_biomarker_series(
    service: BiomarkerServiceDep,
    user: CurrentUser,
) -> list[BiomarkerSeries]:
    """Return each biomarker the caller has measurements for, with its time series.

    Values, units, and reference ranges are verbatim from the lab report;
    canonical_unit is catalogue context. Series are sorted by measurement date
    ascending, so the latest value is the last element.
    """
    return service.list_series(user.id)


@router.get("/biomarker-series/{slug}", operation_id="get_biomarker_series")
def get_biomarker_series(
    service: BiomarkerServiceDep,
    user: CurrentUser,
    slug: str,
) -> BiomarkerSeries:
    """Return one biomarker's time series; empty for a known slug with no data."""
    return service.get_series(user.id, slug)


@router.post(
    "/biomarker-measurements",
    operation_id="create_biomarker_measurements",
    status_code=status.HTTP_201_CREATED,
)
def create_biomarker_measurements(
    service: BiomarkerServiceDep,
    user: CurrentUser,
    payload: Annotated[list[BiomarkerMeasurementCreate], Body(min_length=1)],
) -> list[BiomarkerMeasurementRead]:
    """Record measurements against catalogue biomarkers; all-or-nothing."""
    return service.create_measurements(user.id, payload)


@router.patch(
    "/biomarker-measurements",
    operation_id="update_biomarker_measurements",
)
def update_biomarker_measurements(
    service: BiomarkerServiceDep,
    user: CurrentUser,
    payload: Annotated[BiomarkerMeasurementUpdates, Body(min_length=1)],
) -> list[BiomarkerMeasurementRead]:
    """Update the caller's measurements; omitted fields are left untouched."""
    return service.update_measurements(user.id, payload)


@router.delete(
    "/biomarker-measurements",
    operation_id="delete_biomarker_measurements",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_biomarker_measurements(
    service: BiomarkerServiceDep,
    user: CurrentUser,
    ids: Annotated[list[uuid.UUID], Query(min_length=1)],
) -> None:
    """Delete the caller's measurements; all-or-nothing."""
    service.delete_measurements(user.id, ids)
