import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from mirai_api.core.db import get_session
from mirai_api.core.deps import get_current_user
from mirai_api.main import app
from mirai_api.models import User

TEST_USER_ID = uuid.UUID("00000000-0000-7000-8000-000000000001")


class FakeResult:
    def __init__(self, rows: list) -> None:
        self._rows = rows

    def all(self) -> list:
        return self._rows


class FakeSession:
    """Session stub: canned rows out, writes recorded, no database."""

    def __init__(self) -> None:
        self.rows: list = []
        self.added: list = []
        self.deleted: list = []
        self.executed: list = []
        self.commits = 0
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

    def commit(self) -> None:
        self.commits += 1


@pytest.fixture
def fake_session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def fake_user() -> User:
    return User(
        id=TEST_USER_ID,
        clerk_user_id="user_test",
    )


@pytest.fixture
def client(fake_session: FakeSession, fake_user: User) -> Iterator[TestClient]:
    """Authenticated client; auth and DB dependencies overridden with fakes.

    Instantiated without a context manager so the lifespan (DB warm-up) never
    runs; get_current_user is never exercised (its upsert needs Postgres).
    """
    app.dependency_overrides[get_session] = lambda: fake_session
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(fake_session: FakeSession) -> Iterator[TestClient]:
    """Client with a fake DB but real auth — pins unauthenticated behavior."""
    app.dependency_overrides[get_session] = lambda: fake_session
    yield TestClient(app)
    app.dependency_overrides.clear()
