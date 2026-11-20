import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.db import Base
from app.modules.places.models import Route
from app.modules.users import repository
from app.modules.users.models import AuthSession, User
from tests.factories import finished_route_payload, route_payload

from .conftest import CREDENTIALS, bearer


def delete_account(client, token: str):
    return client.delete("/users/me", headers=bearer(token))


def count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_delete_account_removes_the_user(client, db, tokens):
    response = delete_account(client, tokens["access_token"])

    assert response.status_code == 204
    assert response.content == b""
    assert count(db, User) == 0


def test_deleted_account_tokens_stop_working(client, tokens):
    delete_account(client, tokens["access_token"])

    assert client.get("/users/me", headers=bearer(tokens["access_token"])).status_code == 401
    refresh = client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh.status_code == 401


def test_deleted_account_cannot_sign_in_again(client, tokens):
    delete_account(client, tokens["access_token"])

    assert client.post("/users/login", json=CREDENTIALS).status_code == 401


def test_deleting_closes_the_sessions_of_every_device(client, db, tokens):
    other_device = client.post("/users/login", json=CREDENTIALS).json()

    delete_account(client, tokens["access_token"])

    assert count(db, AuthSession) == 0
    assert client.get("/users/me", headers=bearer(other_device["access_token"])).status_code == 401


def test_deleting_removes_the_active_route_and_the_history(client, db, tokens):
    auth = bearer(tokens["access_token"])
    history = client.post("/places/routes/history", json=finished_route_payload(), headers=auth)
    assert history.status_code == 201
    active = client.put("/places/routes/active", json=route_payload(), headers=auth)
    assert active.status_code == 200
    assert count(db, Route) == 2

    delete_account(client, tokens["access_token"])

    assert count(db, Route) == 0


def test_other_accounts_keep_their_data(client, db, tokens):
    luis = {"email": "luis@example.com", "password": "clave-segura-2"}
    client.post("/users", json=luis)
    luis_tokens = client.post("/users/login", json=luis).json()
    luis_auth = bearer(luis_tokens["access_token"])
    client.put("/places/routes/active", json=route_payload(), headers=luis_auth)

    delete_account(client, tokens["access_token"])

    assert client.get("/users/me", headers=luis_auth).status_code == 200
    assert count(db, Route) == 1


def test_the_email_can_register_a_new_empty_account(client, tokens):
    old_auth = bearer(tokens["access_token"])
    old_id = client.get("/users/me", headers=old_auth).json()["id"]
    client.put("/places/routes/active", json=route_payload(), headers=old_auth)
    delete_account(client, tokens["access_token"])

    assert client.post("/users", json=CREDENTIALS).status_code == 201
    new_tokens = client.post("/users/login", json=CREDENTIALS).json()
    auth = bearer(new_tokens["access_token"])

    assert client.get("/users/me", headers=auth).json()["id"] != old_id
    assert client.get("/places/routes/active", headers=auth).status_code == 404
    assert client.get("/places/routes/history", headers=auth).json()["total"] == 0


def test_delete_account_requires_a_valid_access_token(client, db, tokens):
    assert client.delete("/users/me").status_code == 401
    assert delete_account(client, "no-es-un-jwt").status_code == 401
    assert delete_account(client, tokens["refresh_token"]).status_code == 401
    assert count(db, User) == 1


def test_deleting_twice_with_the_same_token_is_rejected(client, tokens):
    delete_account(client, tokens["access_token"])

    response = delete_account(client, tokens["access_token"])

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_session"


def test_database_failure_keeps_the_account(client, db, tokens, monkeypatch):
    def fail(*_):
        raise IntegrityError("DELETE", {}, Exception("fk"))

    monkeypatch.setattr(repository, "delete_user", fail)

    response = delete_account(client, tokens["access_token"])

    assert response.status_code == 500
    assert response.json()["code"] == "account_deletion_failed"
    assert client.get("/users/me", headers=bearer(tokens["access_token"])).status_code == 200


def test_unavailable_database_is_reported_as_503(client, tokens, monkeypatch):
    def fail(*_):
        raise OperationalError("DELETE", {}, Exception("conexión rechazada"))

    monkeypatch.setattr(repository, "delete_user", fail)

    response = delete_account(client, tokens["access_token"])

    assert response.status_code == 503
    assert response.json()["code"] == "database_unavailable"


@pytest.mark.parametrize(
    "foreign_key",
    [
        fk
        for table in Base.metadata.sorted_tables
        for fk in table.foreign_keys
        if fk.column.table.name == "users"
    ],
    ids=lambda fk: fk.parent.table.name,
)
def test_every_table_that_references_users_is_deleted_in_cascade(foreign_key):
    """Contactos de confianza, eventos SOS y cualquier tabla nueva con datos del usuario
    deben borrarse con la cuenta (SCRUM-7)."""
    assert foreign_key.ondelete == "CASCADE"
