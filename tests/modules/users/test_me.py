from datetime import timedelta

from app.core.security import create_token, decode_token

CREDENTIALS = {"email": "ana@example.com", "password": "clave-segura-1"}


def login(client) -> dict:
    client.post("/users", json=CREDENTIALS)
    return client.post("/users/login", json=CREDENTIALS).json()


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_me_returns_authenticated_user(client):
    tokens = login(client)

    response = client.get("/users/me", headers=bearer(tokens["access_token"]))

    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


def test_me_requires_token(client):
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_me_rejects_malformed_token(client):
    assert client.get("/users/me", headers=bearer("no-es-un-jwt")).status_code == 401


def test_me_rejects_refresh_token_used_as_access(client):
    tokens = login(client)

    response = client.get("/users/me", headers=bearer(tokens["refresh_token"]))

    assert response.status_code == 401


def test_me_rejects_expired_token(client):
    tokens = login(client)
    claims = decode_token(tokens["access_token"])
    expired = create_token(claims["sub"], "access", timedelta(seconds=-1), jti=claims["jti"])

    assert client.get("/users/me", headers=bearer(expired)).status_code == 401


def test_me_rejects_token_without_session(client):
    tokens = login(client)
    claims = decode_token(tokens["access_token"])
    orphan = create_token(claims["sub"], "access", timedelta(minutes=5))

    assert client.get("/users/me", headers=bearer(orphan)).status_code == 401
