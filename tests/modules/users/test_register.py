from sqlalchemy import select

from app.modules.users.models import User

URL = "/users"
VALID = {"email": "ana@example.com", "password": "clave-segura-1"}


def test_register_creates_account(client):
    response = client.post(URL, json=VALID)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert {"id", "created_at"} <= body.keys()
    assert "password" not in body and "password_hash" not in body


def test_register_stores_only_password_hash(client, db):
    client.post(URL, json=VALID)

    user = db.scalar(select(User))
    assert user.password_hash != VALID["password"]
    assert user.password_hash.startswith("$argon2")


def test_register_normalizes_email_case(client):
    response = client.post(URL, json={**VALID, "email": "  Ana@Example.COM "})

    assert response.json()["email"] == "ana@example.com"


def test_register_duplicate_email_returns_conflict_without_leaking_data(client):
    client.post(URL, json=VALID)

    response = client.post(URL, json={**VALID, "email": "ANA@example.com"})

    assert response.status_code == 409
    assert "ana@example.com" not in response.text.lower()


def test_register_rejects_invalid_email(client):
    assert client.post(URL, json={**VALID, "email": "no-es-correo"}).status_code == 422


def test_register_rejects_short_password(client):
    assert client.post(URL, json={**VALID, "password": "corta"}).status_code == 422
