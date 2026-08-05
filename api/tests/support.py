"""Shared test constants and doubles.

Importable from any test module via the `pythonpath = ["tests"]` pytest setting.
Fixtures live in conftest.py; plain values and classes belong here so tests do
not import them out of a pytest plugin module.
"""

import uuid

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


class CommitCountingSession:
    """Session double for service tests: counts commits, holds no state.

    Service tests fake the repositories, so the session is only a transaction
    boundary. Distinct from conftest's FakeSession, which serves router tests
    by canning query results for the real repositories.
    """

    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1
