import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from conftest import TEST_USER_ID
from mirai_api.core.deps import get_biomarker_service
from mirai_api.main import app
from mirai_api.schemas.biomarkers import (
    BiomarkerMeasurementPoint,
    BiomarkerMeasurementRead,
    BiomarkerRead,
    BiomarkerSeries,
)
from mirai_api.services.biomarkers import (
    MeasurementsNotFoundError,
    UnknownBiomarkersError,
)

MEASUREMENT_ID = uuid.UUID("00000000-0000-7000-8000-000000000020")

GLUCOSE = BiomarkerRead(
    slug="glucose",
    display_name="Glucose",
    category="metabolic",
    canonical_unit="mmol/L",
)

GLUCOSE_POINT = BiomarkerMeasurementPoint(
    id=MEASUREMENT_ID,
    measured_at=date(2026, 1, 2),
    value=Decimal("3.1"),
    unit="mmol/L",
    reference_low=None,
    reference_high=Decimal("3.0"),
    lab_upload_id=None,
)

GLUCOSE_READ = BiomarkerMeasurementRead(
    id=MEASUREMENT_ID,
    biomarker_slug="glucose",
    display_name="Glucose",
    value=Decimal("5.4"),
    unit="mmol/L",
    measured_at=date(2026, 7, 12),
    reference_low=None,
    reference_high=None,
    lab_upload_id=None,
)


class StubBiomarkerService:
    """Service stub: canned returns out, calls recorded, optional error raised."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.biomarkers: list[BiomarkerRead] = []
        self.series: list[BiomarkerSeries] = []
        self.reads: list[BiomarkerMeasurementRead] = []
        self.error: Exception | None = None

    def _record(self, *call: object) -> None:
        self.calls.append(call)
        if self.error is not None:
            raise self.error

    def list_biomarkers(self) -> list[BiomarkerRead]:
        self._record("list_biomarkers")
        return self.biomarkers

    def list_series(self, user_id: uuid.UUID) -> list[BiomarkerSeries]:
        self._record("list_series", user_id)
        return self.series

    def get_series(self, user_id: uuid.UUID, slug: str) -> BiomarkerSeries:
        self._record("get_series", user_id, slug)
        return self.series[0]

    def create_measurements(self, user_id: uuid.UUID, items: list) -> list:
        self._record("create_measurements", user_id, items)
        return self.reads

    def update_measurements(self, user_id: uuid.UUID, items: list) -> list:
        self._record("update_measurements", user_id, items)
        return self.reads

    def delete_measurements(self, user_id: uuid.UUID, ids: list) -> None:
        self._record("delete_measurements", user_id, ids)


@pytest.fixture
def stub_service(client: TestClient) -> StubBiomarkerService:
    # The client fixture clears all dependency overrides at teardown.
    stub = StubBiomarkerService()
    app.dependency_overrides[get_biomarker_service] = lambda: stub
    return stub


def test_list_biomarkers_returns_catalogue(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    stub_service.biomarkers = [GLUCOSE]
    response = client.get("/biomarkers")
    assert response.status_code == 200
    assert response.json() == [
        {
            "slug": "glucose",
            "display_name": "Glucose",
            "category": "metabolic",
            "canonical_unit": "mmol/L",
        }
    ]


def test_no_measurements_gives_empty_series_list(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    response = client.get("/biomarker-series")
    assert response.status_code == 200
    assert response.json() == []
    assert stub_service.calls == [("list_series", TEST_USER_ID)]


def test_series_points_expose_ids_and_string_decimals(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    # The generated frontend client types value as string; pin that contract.
    stub_service.series = [
        BiomarkerSeries(
            **GLUCOSE.model_dump(),
            measurements=[GLUCOSE_POINT],
        )
    ]
    (series,) = client.get("/biomarker-series").json()
    (point,) = series["measurements"]
    assert point["id"] == str(MEASUREMENT_ID)
    assert point["value"] == "3.1"
    assert point["reference_high"] == "3.0"
    assert point["reference_low"] is None
    assert point["lab_upload_id"] is None


def test_get_series_unknown_slug_gives_404(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    stub_service.error = UnknownBiomarkersError(["nope"])
    response = client.get("/biomarker-series/nope")
    assert response.status_code == 404


def test_create_measurements_delegates_to_service(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    stub_service.reads = [GLUCOSE_READ]
    response = client.post(
        "/biomarker-measurements",
        json=[
            {
                "biomarker_slug": "glucose",
                "value": "5.4",
                "measured_at": "2026-07-12",
            }
        ],
    )
    assert response.status_code == 201
    (body,) = response.json()
    assert body["id"] == str(MEASUREMENT_ID)
    assert body["value"] == "5.4"
    (name, user_id, items) = stub_service.calls[0]
    assert name == "create_measurements"
    assert user_id == TEST_USER_ID
    assert items[0].biomarker_slug == "glucose"


def test_create_measurements_unknown_slug_gives_404(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    stub_service.error = UnknownBiomarkersError(["nope"])
    response = client.post(
        "/biomarker-measurements",
        json=[
            {
                "biomarker_slug": "nope",
                "value": "5.4",
                "measured_at": "2026-07-12",
            }
        ],
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown biomarkers: nope."


def test_create_measurements_empty_list_gives_422(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    response = client.post("/biomarker-measurements", json=[])
    assert response.status_code == 422
    assert stub_service.calls == []


def test_create_measurements_value_overflow_gives_422(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    # Numeric(12, 4) bounds are enforced at validation, not at commit.
    response = client.post(
        "/biomarker-measurements",
        json=[
            {
                "biomarker_slug": "glucose",
                "value": "1e10",
                "measured_at": "2026-07-12",
            }
        ],
    )
    assert response.status_code == 422
    assert stub_service.calls == []


def test_update_measurements_delegates_to_service(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    stub_service.reads = [GLUCOSE_READ]
    response = client.patch(
        "/biomarker-measurements",
        json=[
            {
                "id": str(MEASUREMENT_ID),
                "value": "5.4",
            }
        ],
    )
    assert response.status_code == 200
    (name, user_id, items) = stub_service.calls[0]
    assert name == "update_measurements"
    assert user_id == TEST_USER_ID
    assert items[0].id == MEASUREMENT_ID


def test_update_measurements_null_value_gives_422(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    # value maps to a non-nullable column; explicit null is a validation error.
    response = client.patch(
        "/biomarker-measurements",
        json=[
            {
                "id": str(MEASUREMENT_ID),
                "value": None,
            }
        ],
    )
    assert response.status_code == 422
    assert stub_service.calls == []


def test_update_measurements_duplicate_ids_give_422(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    # Uniqueness is request-shape validation; the service is never reached.
    response = client.patch(
        "/biomarker-measurements",
        json=[
            {"id": str(MEASUREMENT_ID)},
            {"id": str(MEASUREMENT_ID)},
        ],
    )
    assert response.status_code == 422
    assert stub_service.calls == []


def test_update_measurements_unknown_id_gives_404(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    stub_service.error = MeasurementsNotFoundError([MEASUREMENT_ID])
    response = client.patch(
        "/biomarker-measurements",
        json=[{"id": str(MEASUREMENT_ID)}],
    )
    assert response.status_code == 404


def test_delete_measurements_delegates_to_service(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    response = client.delete(f"/biomarker-measurements?ids={MEASUREMENT_ID}")
    assert response.status_code == 204
    assert stub_service.calls == [
        ("delete_measurements", TEST_USER_ID, [MEASUREMENT_ID]),
    ]


def test_delete_measurements_unknown_id_gives_404(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    stub_service.error = MeasurementsNotFoundError([MEASUREMENT_ID])
    response = client.delete(f"/biomarker-measurements?ids={MEASUREMENT_ID}")
    assert response.status_code == 404


def test_delete_measurements_without_ids_gives_422(
    client: TestClient,
    stub_service: StubBiomarkerService,
) -> None:
    response = client.delete("/biomarker-measurements")
    assert response.status_code == 422
    assert stub_service.calls == []
