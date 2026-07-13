import uuid
from itertools import groupby

from mirai_api.models import Biomarker, BiomarkerMeasurement
from mirai_api.repositories.biomarkers import BiomarkerRepository
from mirai_api.schemas.biomarkers import (
    BiomarkerMeasurementCreate,
    BiomarkerMeasurementPoint,
    BiomarkerMeasurementRead,
    BiomarkerMeasurementUpdate,
    BiomarkerRead,
    BiomarkerSeries,
)


class BiomarkerServiceError(Exception):
    """Base for biomarker domain errors."""


class UnknownBiomarkersError(BiomarkerServiceError):
    def __init__(self, slugs: list[str]) -> None:
        super().__init__(f"Unknown biomarkers: {', '.join(slugs)}.")
        self.slugs = slugs


class MeasurementsNotFoundError(BiomarkerServiceError):
    def __init__(self, ids: list[uuid.UUID]) -> None:
        super().__init__("Measurements not found.")
        self.ids = ids


class BiomarkerService:
    """Application logic for biomarkers; owns the transaction boundary.

    Mutations take the subject user_id (whose data), never the caller: a
    future lab/admin flow authorizes the actor and passes another subject.
    """

    def __init__(self, repo: BiomarkerRepository) -> None:
        self._repo = repo

    def list_biomarkers(self) -> list[BiomarkerRead]:
        return [BiomarkerRead.model_validate(b) for b in self._repo.list_biomarkers()]

    def list_series(self, user_id: uuid.UUID) -> list[BiomarkerSeries]:
        measurements = self._repo.list_measurements(user_id)
        return [
            _series(biomarker, list(points))
            for biomarker, points in groupby(measurements, key=lambda m: m.biomarker)
        ]

    def get_series(self, user_id: uuid.UUID, slug: str) -> BiomarkerSeries:
        # Common case: data exists and already carries its biomarker.
        measurements = self._repo.list_measurements(user_id, slug)
        if measurements:
            return _series(measurements[0].biomarker, measurements)

        # No data: distinguish a known slug (empty series) from an unknown one.
        biomarkers = self._repo.get_biomarkers([slug])
        if not biomarkers:
            raise UnknownBiomarkersError([slug])

        return _series(biomarkers[0], [])

    def create_measurements(
        self,
        user_id: uuid.UUID,
        items: list[BiomarkerMeasurementCreate],
    ) -> list[BiomarkerMeasurementRead]:
        # Resolve every referenced biomarker; reject the whole batch on any unknown slug.
        slugs = {item.biomarker_slug for item in items}
        by_slug = {b.slug: b for b in self._repo.get_biomarkers(slugs)}
        missing = sorted(slugs - by_slug.keys())
        if missing:
            raise UnknownBiomarkersError(missing)

        # Build the rows; unit falls back to the biomarker's canonical unit.
        measurements = []
        for item in items:
            biomarker = by_slug[item.biomarker_slug]
            measurements.append(
                BiomarkerMeasurement(
                    user_id=user_id,
                    biomarker=biomarker,
                    lab_upload_id=None,
                    value=item.value,
                    unit=item.unit or biomarker.canonical_unit,
                    reference_low=item.reference_low,
                    reference_high=item.reference_high,
                    measured_at=item.measured_at,
                )
            )

        # Persist as one transaction; the flush gives the rows their ids.
        self._repo.add_measurements(measurements)
        self._repo.commit()
        return [_read(m) for m in measurements]

    def update_measurements(
        self,
        user_id: uuid.UUID,
        items: list[BiomarkerMeasurementUpdate],
    ) -> list[BiomarkerMeasurementRead]:
        # Fetch the targets scoped to the user; a miss is unknown and not-owned alike.
        ids = [item.id for item in items]
        by_id = {m.id: m for m in self._repo.get_measurements(user_id, ids)}
        missing = sorted(set(ids) - by_id.keys())
        if missing:
            raise MeasurementsNotFoundError(missing)

        # Apply only the fields each item explicitly set.
        for item in items:
            for field, value in item.model_dump(exclude_unset=True, exclude={"id"}).items():
                setattr(by_id[item.id], field, value)

        # Commit once; return the updated rows in request order.
        self._repo.commit()
        return [_read(by_id[item.id]) for item in items]

    def delete_measurements(
        self,
        user_id: uuid.UUID,
        ids: list[uuid.UUID],
    ) -> None:
        # One DELETE; the returned ids reveal what actually existed for this user.
        requested = set(ids)
        deleted = self._repo.delete_measurements(user_id, requested)

        # Any miss aborts before commit, rolling the partial delete back.
        if deleted != requested:
            raise MeasurementsNotFoundError(sorted(requested - deleted))

        self._repo.commit()


def _series(
    biomarker: Biomarker,
    measurements: list[BiomarkerMeasurement],
) -> BiomarkerSeries:
    return BiomarkerSeries(
        **BiomarkerRead.model_validate(biomarker).model_dump(),
        measurements=[BiomarkerMeasurementPoint.model_validate(m) for m in measurements],
    )


def _read(measurement: BiomarkerMeasurement) -> BiomarkerMeasurementRead:
    return BiomarkerMeasurementRead(
        **BiomarkerMeasurementPoint.model_validate(measurement).model_dump(),
        biomarker_slug=measurement.biomarker.slug,
        display_name=measurement.biomarker.display_name,
    )
