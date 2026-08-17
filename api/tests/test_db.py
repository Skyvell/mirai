"""Tests for the request transaction boundary.

Services no longer commit, so `transaction` is the only thing that does. Routes
whose service provider is stubbed never resolve `get_session`, so the cases that
need a live boundary get routes of their own here. `test_me.py` covers the plain
commit-on-success path on a real endpoint.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mirai_api.core.db import get_session, transaction
from mirai_api.core.deps import DbSession
from support import FakeSession, session_override


def test_rolls_back_and_reraises_on_error() -> None:
    session = FakeSession()
    with pytest.raises(RuntimeError), transaction(session):  # type: ignore[arg-type]
        raise RuntimeError("boom")
    assert (session.commits, session.rollbacks) == (0, 1)


def _failing_client(session: FakeSession) -> TestClient:
    """A route that stages a write, then fails, as two service calls would."""
    api = FastAPI()

    @api.post("/composed")
    def composed(db: DbSession) -> dict:
        db.add("first")
        raise RuntimeError("second call failed")

    api.dependency_overrides[get_session] = session_override(session)
    return TestClient(api, raise_server_exceptions=False)


def test_composed_calls_discard_the_first_when_the_second_fails() -> None:
    session = FakeSession()
    response = _failing_client(session).post("/composed")
    assert response.status_code == 500
    assert session.added == ["first"]

    # The point of the change: the first write never reaches the database.
    assert (session.commits, session.rollbacks) == (0, 1)


class FailingCommitSession(FakeSession):
    def commit(self) -> None:
        raise RuntimeError("commit failed")


def test_a_failed_commit_reaches_the_client() -> None:
    """Pins scope="function" on DbSession, which nothing else would catch.

    Under the default "request" scope the commit runs after the response has
    been sent, so this would be a 200 and a failed write would go unreported.
    """
    api = FastAPI()

    @api.get("/ok")
    def ok(db: DbSession) -> str:
        return "ok"

    api.dependency_overrides[get_session] = session_override(FailingCommitSession())
    response = TestClient(api, raise_server_exceptions=False).get("/ok")

    assert response.status_code == 500
