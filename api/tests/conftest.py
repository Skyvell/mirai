from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from mirai_api.core.db import get_session
from mirai_api.core.deps import get_current_user
from mirai_api.main import app
from mirai_api.models import User
from support import TEST_USER_ID, FakeSession, session_override


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
    app.dependency_overrides[get_session] = session_override(fake_session)
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(fake_session: FakeSession) -> Iterator[TestClient]:
    """Client with a fake DB but real auth — pins unauthenticated behavior."""
    app.dependency_overrides[get_session] = session_override(fake_session)
    yield TestClient(app)
    app.dependency_overrides.clear()
