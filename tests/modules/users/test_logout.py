CREDENTIALS = {"email": "ana@example.com", "password": "clave-segura-1"}


def login(client) -> dict:
    client.post("/users", json=CREDENTIALS)
    return client.post("/users/login", json=CREDENTIALS).json()


def logout(client, token: str):
    return client.post("/users/logout", json={"refresh_token": token})


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_logout_invalidates_access_and_refresh_tokens(client):
    tokens = login(client)

    assert logout(client, tokens["refresh_token"]).status_code == 204

    assert client.get("/users/me", headers=bearer(tokens["access_token"])).status_code == 401
    refresh = client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 401


def test_logout_only_closes_the_given_device_session(client):
    first = login(client)
    second = client.post("/users/login", json=CREDENTIALS).json()

    logout(client, first["refresh_token"])

    assert client.get("/users/me", headers=bearer(second["access_token"])).status_code == 200


def test_logout_twice_is_rejected(client):
    tokens = login(client)
    logout(client, tokens["refresh_token"])

    assert logout(client, tokens["refresh_token"]).status_code == 401


def test_logout_rejects_access_token_and_garbage(client):
    tokens = login(client)

    assert logout(client, tokens["access_token"]).status_code == 401
    assert logout(client, "no-es-un-jwt").status_code == 401
