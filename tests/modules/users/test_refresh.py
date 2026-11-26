from .conftest import bearer


def refresh(client, token: str):
    return client.post("/users/refresh", json={"refresh_token": token})


def test_refresh_returns_new_working_tokens(client, tokens):
    response = refresh(client, tokens["refresh_token"])

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert client.get("/users/me", headers=bearer(new_tokens["access_token"])).status_code == 200


def test_refresh_rotates_and_revokes_previous_session(client, tokens):
    refresh(client, tokens["refresh_token"])

    assert refresh(client, tokens["refresh_token"]).status_code == 401
    assert client.get("/users/me", headers=bearer(tokens["access_token"])).status_code == 401


def test_refresh_rejects_access_token(client, tokens):
    assert refresh(client, tokens["access_token"]).status_code == 401


def test_refresh_rejects_malformed_token(client):
    assert refresh(client, "no-es-un-jwt").status_code == 401
