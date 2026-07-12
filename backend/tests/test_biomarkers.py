import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from conftest import FakeSession
from mirai_api.models import Biomarker


def _row(**overrides: object) -> SimpleNamespace:
    """A stub of one joined biomarker/measurement row, attribute-compatible."""
    base: dict = {
        "slug": "ldl_cholesterol",
        "display_name": "LDL Cholesterol",
        "category": "lipids",
        "canonical_unit": "mmol/L",
        "measured_at": date(2026, 1, 2),
        "value": Decimal("3.1"),
        "unit": "mmol/L",
        "reference_low": None,
        "reference_high": Decimal("3.0"),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_no_measurements_gives_empty_list(client: TestClient) -> None:
    response = client.get("/biomarkers")
    assert response.status_code == 200
    assert response.json() == []


def test_rows_group_into_series_per_biomarker(
    client: TestClient,
    fake_session: FakeSession,
) -> None:
    # Pre-ordered as the SQL ORDER BY would return them.
    fake_session.rows = [
        _row(measured_at=date(2026, 1, 2)),
        _row(
            measured_at=date(2026, 3, 2),
            value=Decimal("2.8"),
        ),
        _row(
            slug="glucose",
            display_name="Glucose",
            category="metabolic",
            unit="mmol/L",
            value=Decimal("5.4"),
        ),
    ]
    response = client.get("/biomarkers")
    assert response.status_code == 200
    series = response.json()
    assert [s["slug"] for s in series] == ["ldl_cholesterol", "glucose"]
    assert [m["measured_at"] for m in series[0]["measurements"]] == [
        "2026-01-02",
        "2026-03-02",
    ]
    assert len(series[1]["measurements"]) == 1


def test_decimal_values_serialize_as_json_strings(
    client: TestClient,
    fake_session: FakeSession,
) -> None:
    # The generated frontend client types value as string; pin that contract.
    fake_session.rows = [_row()]
    point = client.get("/biomarkers").json()[0]["measurements"][0]
    assert point["value"] == "3.1"
    assert point["reference_high"] == "3.0"
    assert point["reference_low"] is None


def _catalogue_biomarker() -> Biomarker:
    return Biomarker(
        id=uuid.UUID("00000000-0000-7000-8000-000000000002"),
        slug="glucose",
        display_name="Glucose",
        category="metabolic",
        canonical_unit="mmol/L",
    )


def test_catalog_returns_all_biomarkers(
    client: TestClient,
    fake_session: FakeSession,
) -> None:
    fake_session.rows = [
        SimpleNamespace(
            slug="glucose",
            display_name="Glucose",
            category="metabolic",
            canonical_unit="mmol/L",
        ),
    ]
    response = client.get("/biomarkers/catalog")
    assert response.status_code == 200
    assert response.json() == [
        {
            "slug": "glucose",
            "display_name": "Glucose",
            "category": "metabolic",
            "canonical_unit": "mmol/L",
        }
    ]


def test_create_measurement_unknown_slug_gives_404(client: TestClient) -> None:
    response = client.post(
        "/biomarkers/nope/measurements",
        json={
            "value": "5.4",
            "measured_at": "2026-07-12",
        },
    )
    assert response.status_code == 404


def test_create_measurement_defaults_unit_to_canonical(
    client: TestClient,
    fake_session: FakeSession,
) -> None:
    fake_session.scalar_value = _catalogue_biomarker()
    response = client.post(
        "/biomarkers/glucose/measurements",
        json={
            "value": "5.4",
            "measured_at": "2026-07-12",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["unit"] == "mmol/L"
    assert body["value"] == "5.4"
    (measurement,) = fake_session.added
    assert measurement.lab_upload_id is None
    assert measurement.unit == "mmol/L"
    assert fake_session.commits == 1


def test_create_measurement_keeps_explicit_unit(
    client: TestClient,
    fake_session: FakeSession,
) -> None:
    fake_session.scalar_value = _catalogue_biomarker()
    response = client.post(
        "/biomarkers/glucose/measurements",
        json={
            "value": "97",
            "unit": "mg/dL",
            "measured_at": "2026-07-12",
        },
    )
    assert response.status_code == 201
    assert response.json()["unit"] == "mg/dL"
