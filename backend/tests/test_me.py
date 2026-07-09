from fastapi.testclient import TestClient

from mirai_api.users.models import User


def test_me_returns_identity(client: TestClient, fake_user: User) -> None:
    response = client.get("/me")
    assert response.status_code == 200
    assert response.json() == {
        "user_id": str(fake_user.id),
        "clerk_user_id": fake_user.clerk_user_id,
    }


def test_me_without_token_is_rejected(unauthenticated_client: TestClient) -> None:
    # HTTPBearer(auto_error=True) rejects before any JWKS or DB access.
    response = unauthenticated_client.get("/me")
    assert response.status_code == 401
