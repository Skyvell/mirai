from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from conftest import FakeSession


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
