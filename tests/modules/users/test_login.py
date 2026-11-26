from sqlalchemy import select

from app.core.security import decode_token
from app.modules.users.models import AuthSession, User

from .conftest import CREDENTIALS


def register(client):
    assert client.post("/users", json=CREDENTIALS).status_code == 201


def test_login_returns_token_pair_bound_to_a_session(client, db):
    register(client)

    response = client.post("/users/login", json=CREDENTIALS)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    access, refresh = decode_token(body["access_token"]), decode_token(body["refresh_token"])
    assert (access["type"], refresh["type"]) == ("access", "refresh")
    session = db.scalar(select(AuthSession))
    assert access["jti"] == refresh["jti"] == str(session.id)
    assert access["sub"] == str(session.user_id)


def test_login_is_case_insensitive_on_email(client):
    register(client)

    response = client.post("/users/login", json={**CREDENTIALS, "email": "ANA@example.com"})

    assert response.status_code == 200


def test_login_wrong_password_and_unknown_email_look_the_same(client):
    register(client)

    wrong_password = client.post("/users/login", json={**CREDENTIALS, "password": "otra-clave-1"})
    unknown_email = client.post("/users/login", json={**CREDENTIALS, "email": "nadie@example.com"})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_login_rejects_account_without_password(client, db):
    db.add(User(email="google@example.com", google_sub="sub-1"))
    db.commit()

    response = client.post("/users/login", json={**CREDENTIALS, "email": "google@example.com"})

    assert response.status_code == 401


def test_failed_login_does_not_create_session(client, db):
    register(client)

    client.post("/users/login", json={**CREDENTIALS, "password": "otra-clave-1"})

    assert db.scalar(select(AuthSession)) is None


def test_dummy_hash_password_never_signs_in_an_account_without_password(client, db):
    """Regresión: la contraseña del hash señuelo (pública en el repo) daba acceso a
    cualquier cuenta solo de Google conociendo su correo."""
    db.add(User(email="google@example.com", google_sub="sub-1"))
    db.commit()

    response = client.post(
        "/users/login", json={"email": "google@example.com", "password": "lumio-dummy-password"}
    )

    assert response.status_code == 401
    assert db.scalar(select(AuthSession)) is None
