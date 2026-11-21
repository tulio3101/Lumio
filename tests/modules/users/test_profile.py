import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app.modules.users import repository

from .conftest import CREDENTIALS, bearer


def update(client, token: str, body: dict):
    return client.patch("/users/me", json=body, headers=bearer(token))


def me(client, token: str) -> dict:
    return client.get("/users/me", headers=bearer(token)).json()


def test_new_account_has_an_empty_profile(client, tokens):
    profile = me(client, tokens["access_token"])

    assert profile["email"] == "ana@example.com"
    assert profile["display_name"] is None
    assert profile["phone"] is None


def test_profile_changes_are_saved_and_returned(client, tokens):
    response = update(
        client, tokens["access_token"], {"display_name": "Ana María", "phone": "3001234567"}
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Ana María"
    assert response.json()["phone"] == "3001234567"
    assert me(client, tokens["access_token"]) == response.json()


def test_values_are_normalized_before_saving(client, tokens):
    response = update(
        client,
        tokens["access_token"],
        {"display_name": "  Ana   O'Neill-Pérez ", "phone": "300 123-4567"},
    )

    assert response.json()["display_name"] == "Ana O'Neill-Pérez"
    assert response.json()["phone"] == "3001234567"


def test_only_the_sent_fields_change(client, tokens):
    update(client, tokens["access_token"], {"display_name": "Ana", "phone": "3001234567"})

    response = update(client, tokens["access_token"], {"phone": "3109876543"})

    assert response.json()["display_name"] == "Ana"
    assert response.json()["phone"] == "3109876543"


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_null_or_blank_removes_a_value(client, tokens, empty):
    update(client, tokens["access_token"], {"display_name": "Ana", "phone": "3001234567"})

    response = update(client, tokens["access_token"], {"display_name": empty, "phone": empty})

    assert response.json()["display_name"] is None
    assert response.json()["phone"] is None


@pytest.mark.parametrize(
    "body",
    [
        {"display_name": "R2-D2"},
        {"display_name": "Ana <script>"},
        {"display_name": "..."},
        {"display_name": "A" * 61},
        {"phone": "2001234567"},
        {"phone": "300123456"},
        {"phone": "30012345678"},
        {"phone": "+573001234567"},
        {"phone": "300abc4567"},
        {"email": "otro@example.com"},
        {"password_hash": "x"},
    ],
)
def test_invalid_data_is_rejected_and_nothing_changes(client, tokens, body):
    update(client, tokens["access_token"], {"display_name": "Ana", "phone": "3001234567"})

    response = update(client, tokens["access_token"], body)

    assert response.status_code == 422
    profile = me(client, tokens["access_token"])
    assert profile["email"] == "ana@example.com"
    assert (profile["display_name"], profile["phone"]) == ("Ana", "3001234567")


def test_one_invalid_field_rejects_the_whole_change(client, tokens):
    response = update(client, tokens["access_token"], {"display_name": "Ana", "phone": "123"})

    assert response.status_code == 422
    assert me(client, tokens["access_token"])["display_name"] is None


def test_sixty_characters_and_accents_are_allowed(client, tokens):
    name = "Ñ" + "á" * 59

    assert (
        update(client, tokens["access_token"], {"display_name": name}).json()["display_name"]
        == name
    )


def test_profile_requires_a_valid_access_token(client, tokens):
    assert client.patch("/users/me", json={"display_name": "Ana"}).status_code == 401
    assert update(client, tokens["refresh_token"], {"display_name": "Ana"}).status_code == 401


def test_each_account_only_changes_its_own_profile(client, tokens):
    luis = {"email": "luis@example.com", "password": "clave-segura-2"}
    client.post("/users", json=luis)
    luis_token = client.post("/users/login", json=luis).json()["access_token"]

    update(client, luis_token, {"display_name": "Luis"})

    assert me(client, tokens["access_token"])["display_name"] is None


def test_database_failure_keeps_the_profile(client, tokens, monkeypatch):
    def fail(*_):
        raise IntegrityError("UPDATE", {}, Exception("fallo"))

    monkeypatch.setattr(repository, "update_profile", fail)

    response = update(client, tokens["access_token"], {"display_name": "Ana"})

    assert response.status_code == 500
    assert response.json()["code"] == "profile_update_failed"


def test_unavailable_database_is_reported_as_503(client, tokens, monkeypatch):
    def fail(*_):
        raise OperationalError("UPDATE", {}, Exception("conexión rechazada"))

    monkeypatch.setattr(repository, "update_profile", fail)

    response = update(client, tokens["access_token"], {"display_name": "Ana"})

    assert response.status_code == 503
    assert response.json()["code"] == "database_unavailable"


# MARK: Cambiar contraseña

NEW_PASSWORD = "otra-clave-segura"


def change_password(client, token: str, current: str, new: str = NEW_PASSWORD):
    return client.put(
        "/users/me/password",
        json={"current_password": current, "new_password": new},
        headers=bearer(token),
    )


def login(client, password: str):
    return client.post("/users/login", json={**CREDENTIALS, "password": password})


def test_password_change_replaces_the_password(client, tokens):
    response = change_password(client, tokens["access_token"], CREDENTIALS["password"])

    assert response.status_code == 204
    assert login(client, CREDENTIALS["password"]).status_code == 401
    assert login(client, NEW_PASSWORD).status_code == 200


def test_password_change_keeps_this_device_and_closes_the_others(client, tokens):
    other = client.post("/users/login", json=CREDENTIALS).json()

    change_password(client, tokens["access_token"], CREDENTIALS["password"])

    assert client.get("/users/me", headers=bearer(tokens["access_token"])).status_code == 200
    refreshed = client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert client.get("/users/me", headers=bearer(other["access_token"])).status_code == 401
    other_refresh = client.post("/users/refresh", json={"refresh_token": other["refresh_token"]})
    assert other_refresh.status_code == 401


def test_wrong_current_password_is_rejected_with_403(client, tokens):
    response = change_password(client, tokens["access_token"], "no-es-la-clave")

    assert response.status_code == 403
    assert response.json()["code"] == "invalid_current_password"
    assert login(client, CREDENTIALS["password"]).status_code == 200


def test_new_password_must_be_different(client, tokens):
    response = change_password(
        client, tokens["access_token"], CREDENTIALS["password"], CREDENTIALS["password"]
    )

    assert response.status_code == 422
    assert response.json()["code"] == "password_unchanged"


@pytest.mark.parametrize("new", ["corta", "x" * 129])
def test_new_password_follows_the_sign_up_rules(client, tokens, new):
    response = change_password(client, tokens["access_token"], CREDENTIALS["password"], new)

    assert response.status_code == 422
    assert login(client, CREDENTIALS["password"]).status_code == 200


def test_accounts_without_password_cannot_change_it(client, db, tokens):
    user = repository.get_by_email(db, CREDENTIALS["email"])
    user.password_hash = None
    db.commit()

    response = change_password(client, tokens["access_token"], "lo-que-sea")

    assert response.status_code == 409
    assert response.json()["code"] == "password_not_set"


def test_password_change_requires_a_valid_access_token(client, tokens):
    assert client.put("/users/me/password", json={}).status_code == 401
    assert (
        change_password(client, tokens["refresh_token"], CREDENTIALS["password"]).status_code == 401
    )


def test_password_change_failure_keeps_the_old_password(client, tokens, monkeypatch):
    def fail(*_):
        raise IntegrityError("UPDATE", {}, Exception("fallo"))

    monkeypatch.setattr(repository, "change_password", fail)

    response = change_password(client, tokens["access_token"], CREDENTIALS["password"])

    assert response.status_code == 500
    assert response.json()["code"] == "password_change_failed"
    assert login(client, CREDENTIALS["password"]).status_code == 200


def test_decomposed_accents_are_stored_composed(client, tokens):
    response = update(client, tokens["access_token"], {"display_name": "Jose\u0301"})

    assert response.status_code == 200
    assert response.json()["display_name"] == "Jos\u00e9"
