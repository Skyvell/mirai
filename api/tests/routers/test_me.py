from fastapi.testclient import TestClient

from mirai_api.models import User
from support import FakeSession


def test_me_returns_identity_and_profile(client: TestClient, fake_user: User) -> None:
    response = client.get("/me")
    assert response.status_code == 200
    assert response.json() == {
        "user_id": str(fake_user.id),
        "clerk_user_id": fake_user.clerk_user_id,
        "sex": None,
        "date_of_birth": None,
    }


def test_me_without_token_is_rejected(unauthenticated_client: TestClient) -> None:
    # HTTPBearer(auto_error=True) rejects before any JWKS or DB access.
    response = unauthenticated_client.get("/me")
    assert response.status_code == 401


def test_patch_me_sets_profile(
    client: TestClient,
    fake_user: User,
    fake_session: FakeSession,
) -> None:
    response = client.patch(
        "/me",
        json={"sex": "female", "date_of_birth": "1990-04-12"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "user_id": str(fake_user.id),
        "clerk_user_id": fake_user.clerk_user_id,
        "sex": "female",
        "date_of_birth": "1990-04-12",
    }

    # UserService does not commit; the request boundary does, once.
    assert (fake_session.commits, fake_session.rollbacks) == (1, 0)


def test_patch_me_rejects_future_birth_date(
    client: TestClient,
    fake_session: FakeSession,
) -> None:
    response = client.patch(
        "/me",
        json={"sex": "male", "date_of_birth": "2999-01-01"},
    )
    assert response.status_code == 422

    # The session is opened before the body is validated, so a rejected request
    # unwinds the boundary rather than committing.
    assert (fake_session.commits, fake_session.rollbacks) == (0, 1)


def test_patch_me_rejects_unknown_sex(client: TestClient) -> None:
    response = client.patch(
        "/me",
        json={"sex": "other", "date_of_birth": "1990-04-12"},
    )
    assert response.status_code == 422
