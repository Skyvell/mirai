import uuid
from collections.abc import Iterable
from datetime import date
from decimal import Decimal

import pytest

from conftest import TEST_USER_ID
from mirai_api.models import Biomarker, BiomarkerMeasurement
from mirai_api.schemas.biomarkers import (
    BiomarkerMeasurementCreate,
    BiomarkerMeasurementUpdate,
)
from mirai_api.services.biomarkers import (
    BiomarkerService,
    MeasurementsNotFoundError,
    UnknownBiomarkersError,
)

GLUCOSE = Biomarker(
    id=uuid.UUID("00000000-0000-7000-8000-000000000002"),
    slug="glucose",
    display_name="Glucose",
    category="metabolic",
    canonical_unit="mmol/L",
)

LDL = Biomarker(
    id=uuid.UUID("00000000-0000-7000-8000-000000000003"),
    slug="ldl_cholesterol",
    display_name="LDL Cholesterol",
    category="lipids",
    canonical_unit="mmol/L",
)


def _measurement(
    biomarker: Biomarker,
    **overrides: object,
) -> BiomarkerMeasurement:
    fields: dict = {
        "id": uuid.uuid7(),
        "user_id": TEST_USER_ID,
        "biomarker": biomarker,
        "lab_upload_id": None,
        "value": Decimal("3.1"),
        "unit": "mmol/L",
        "reference_low": None,
        "reference_high": None,
        "measured_at": date(2026, 1, 2),
    }
    fields.update(overrides)
    return BiomarkerMeasurement(**fields)


class FakeBiomarkerRepository:
    """Repository fake: in-memory lists, commits counted."""

    def __init__(
        self,
        biomarkers: list[Biomarker] | None = None,
        measurements: list[BiomarkerMeasurement] | None = None,
    ) -> None:
        self.biomarkers = biomarkers or []
        self.measurements = measurements or []
        self.added: list[BiomarkerMeasurement] = []
        self.commits = 0

    def list_biomarkers(self) -> list[Biomarker]:
        return list(self.biomarkers)

    def get_biomarkers(self, slugs: Iterable[str]) -> list[Biomarker]:
        wanted = set(slugs)
        return [b for b in self.biomarkers if b.slug in wanted]

    def list_measurements(
        self,
        user_id: uuid.UUID,
        slug: str | None = None,
    ) -> list[BiomarkerMeasurement]:
        return [
            m
            for m in self.measurements
            if m.user_id == user_id and (slug is None or m.biomarker.slug == slug)
        ]

    def get_measurements(
        self,
        user_id: uuid.UUID,
        ids: Iterable[uuid.UUID],
    ) -> list[BiomarkerMeasurement]:
        wanted = set(ids)
        return [m for m in self.measurements if m.user_id == user_id and m.id in wanted]

    def add_measurements(self, measurements: list[BiomarkerMeasurement]) -> None:
        for m in measurements:
            if m.id is None:
                m.id = uuid.uuid7()
        self.added.extend(measurements)
        self.measurements.extend(measurements)

    def delete_measurements(
        self,
        user_id: uuid.UUID,
        ids: Iterable[uuid.UUID],
    ) -> set[uuid.UUID]:
        wanted = set(ids)
        deleted = {m.id for m in self.measurements if m.user_id == user_id and m.id in wanted}
        self.measurements = [m for m in self.measurements if m.id not in deleted]
        return deleted

    def commit(self) -> None:
        self.commits += 1


def _service(repo: FakeBiomarkerRepository) -> BiomarkerService:
    return BiomarkerService(repo)  # type: ignore[arg-type]


def test_create_defaults_unit_to_canonical() -> None:
    repo = FakeBiomarkerRepository(biomarkers=[GLUCOSE])
    created = _service(repo).create_measurements(
        TEST_USER_ID,
        [
            BiomarkerMeasurementCreate(
                biomarker_slug="glucose",
                value=Decimal("5.4"),
                measured_at=date(2026, 7, 12),
            )
        ],
    )
    (read,) = created
    assert read.unit == "mmol/L"
    assert read.id is not None
    assert read.lab_upload_id is None
    (added,) = repo.added
    assert added.user_id == TEST_USER_ID
    assert repo.commits == 1


def test_create_keeps_explicit_unit() -> None:
    repo = FakeBiomarkerRepository(biomarkers=[GLUCOSE])
    (read,) = _service(repo).create_measurements(
        TEST_USER_ID,
        [
            BiomarkerMeasurementCreate(
                biomarker_slug="glucose",
                value=Decimal("97"),
                unit="mg/dL",
                measured_at=date(2026, 7, 12),
            )
        ],
    )
    assert read.unit == "mg/dL"


def test_create_unknown_slug_raises_before_commit() -> None:
    repo = FakeBiomarkerRepository(biomarkers=[GLUCOSE])
    with pytest.raises(UnknownBiomarkersError) as exc_info:
        _service(repo).create_measurements(
            TEST_USER_ID,
            [
                BiomarkerMeasurementCreate(
                    biomarker_slug="nope",
                    value=Decimal("1"),
                    measured_at=date(2026, 7, 12),
                )
            ],
        )
    assert exc_info.value.slugs == ["nope"]
    assert repo.added == []
    assert repo.commits == 0


def test_list_series_groups_contiguous_measurements() -> None:
    # Pre-ordered as the repository ORDER BY would return them.
    repo = FakeBiomarkerRepository(
        measurements=[
            _measurement(LDL, measured_at=date(2026, 1, 2)),
            _measurement(LDL, measured_at=date(2026, 3, 2), value=Decimal("2.8")),
            _measurement(GLUCOSE, value=Decimal("5.4")),
        ]
    )
    series = _service(repo).list_series(TEST_USER_ID)
    assert [s.slug for s in series] == ["ldl_cholesterol", "glucose"]
    assert [m.measured_at for m in series[0].measurements] == [
        date(2026, 1, 2),
        date(2026, 3, 2),
    ]
    assert len(series[1].measurements) == 1
    assert series[1].measurements[0].id is not None


def test_get_series_unknown_slug_raises() -> None:
    repo = FakeBiomarkerRepository(biomarkers=[GLUCOSE])
    with pytest.raises(UnknownBiomarkersError):
        _service(repo).get_series(TEST_USER_ID, "nope")


def test_get_series_known_slug_without_data_is_empty() -> None:
    repo = FakeBiomarkerRepository(biomarkers=[GLUCOSE])
    series = _service(repo).get_series(TEST_USER_ID, "glucose")
    assert series.slug == "glucose"
    assert series.measurements == []


def test_update_applies_only_set_fields() -> None:
    measurement = _measurement(GLUCOSE)
    repo = FakeBiomarkerRepository(measurements=[measurement])
    (read,) = _service(repo).update_measurements(
        TEST_USER_ID,
        [
            BiomarkerMeasurementUpdate(
                id=measurement.id,
                value=Decimal("4.2"),
            )
        ],
    )
    assert read.value == Decimal("4.2")
    # Omitted fields stay untouched.
    assert measurement.unit == "mmol/L"
    assert measurement.measured_at == date(2026, 1, 2)
    assert repo.commits == 1


def test_update_explicit_null_clears_nullable_field() -> None:
    measurement = _measurement(GLUCOSE, reference_high=Decimal("3.0"))
    repo = FakeBiomarkerRepository(measurements=[measurement])
    _service(repo).update_measurements(
        TEST_USER_ID,
        [
            BiomarkerMeasurementUpdate.model_validate(
                {
                    "id": measurement.id,
                    "reference_high": None,
                }
            )
        ],
    )
    assert measurement.reference_high is None


def test_update_foreign_measurement_raises_not_found() -> None:
    # Another user's row: same error as a nonexistent id, no existence leak.
    foreign = _measurement(GLUCOSE, user_id=uuid.uuid7())
    repo = FakeBiomarkerRepository(measurements=[foreign])
    with pytest.raises(MeasurementsNotFoundError):
        _service(repo).update_measurements(
            TEST_USER_ID,
            [BiomarkerMeasurementUpdate(id=foreign.id)],
        )
    assert repo.commits == 0


def test_delete_removes_owned_measurements() -> None:
    measurement = _measurement(GLUCOSE)
    repo = FakeBiomarkerRepository(measurements=[measurement])
    _service(repo).delete_measurements(TEST_USER_ID, [measurement.id])
    assert repo.measurements == []
    assert repo.commits == 1


def test_delete_partial_match_raises_before_commit() -> None:
    measurement = _measurement(GLUCOSE)
    repo = FakeBiomarkerRepository(measurements=[measurement])
    with pytest.raises(MeasurementsNotFoundError):
        _service(repo).delete_measurements(
            TEST_USER_ID,
            [measurement.id, uuid.uuid7()],
        )
    assert repo.commits == 0
