"""Shared test constants and doubles.

Importable from any test module via the `pythonpath = ["tests"]` pytest setting.
Fixtures live in conftest.py; plain values and classes belong here so tests do
not import them out of a pytest plugin module.
"""

import uuid
from collections.abc import Callable, Iterator

from mirai_api.core.db import transaction
from mirai_api.models import Biomarker

TEST_USER_ID = uuid.UUID("00000000-0000-7000-8000-000000000001")

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


class FakeResult:
    def __init__(self, rows: list) -> None:
        self._rows = rows

    def all(self) -> list:
        return self._rows


class FakeSession:
    """Session stub: canned rows out, writes and transaction calls recorded, no database."""

    def __init__(self) -> None:
        self.rows: list = []
        self.added: list = []
        self.deleted: list = []
        self.executed: list = []
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0
        self.scalar_value: object = None

    def execute(self, stmt: object) -> FakeResult:
        self.executed.append(stmt)
        return FakeResult(self.rows)

    def scalar(self, stmt: object) -> object:
        return self.scalar_value

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def add_all(self, objs: object) -> None:
        self.added.extend(objs)

    def delete(self, obj: object) -> None:
        self.deleted.append(obj)

    def flush(self) -> None:
        self.flushes += 1

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def session_override(session: FakeSession) -> Callable[[], Iterator[FakeSession]]:
    """Serve the fake through the real transaction helper; a lambda would skip it."""

    def override() -> Iterator[FakeSession]:
        with transaction(session):
            yield session

    return override
