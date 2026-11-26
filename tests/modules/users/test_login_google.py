"""Iniciar sesión / Crear cuenta con Google (SCRUM-62 / SCRUM-68).

El endpoint se prueba con un verificador falso; la verificación real del ID token está en
test_google_auth.py. Las cuentas solo de Google (google_sub, sin password_hash) no pueden
usar los flujos de contraseña.
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.security import decode_token
from app.main import app
from app.modules.users import service
from app.modules.users.google_auth import (
    GoogleAuthUnavailable,
    GoogleIdentity,
    InvalidGoogleToken,
    UnconfiguredGoogleVerifier,
    get_google_verifier,
)
from app.modules.users.models import AuthSession, User

from .conftest import CREDENTIALS, bearer

GOOGLE_LOGIN = "/users/login/google"
ANA = GoogleIdentity(sub="google-sub-ana", email="Ana.Google@Example.com", email_verified=True)


class FakeVerifier:
    """Acepta los tokens registrados en ``identities``; el resto es inválido."""

    def __init__(self) -> None:
        self.identities: dict[str, GoogleIdentity] = {"token-ana": ANA}
        self.error: Exception | None = None

    def verify(self, token: str) -> GoogleIdentity:
        if self.error:
            raise self.error
        if token not in self.identities:
            raise InvalidGoogleToken("desconocido")
        return self.identities[token]


@pytest.fixture
def google(client) -> FakeVerifier:
    verifier = FakeVerifier()
    app.dependency_overrides[get_google_verifier] = lambda: verifier
    return verifier


def count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def sign_in(client, token: str = "token-ana"):
    return client.post(GOOGLE_LOGIN, json={"id_token": token})


# --- Crear cuenta e iniciar sesión ---------------------------------------------------------


def test_first_google_sign_in_creates_account_without_password(client, db, google):
    response = sign_in(client)

    assert response.status_code == 201
    user = db.scalar(select(User))
    assert user.email == "ana.google@example.com"
    assert user.google_sub == ANA.sub
    assert user.password_hash is None


def test_google_sign_in_returns_token_pair_bound_to_a_session(client, db, google):
    body = sign_in(client).json()

    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    access, refresh = decode_token(body["access_token"]), decode_token(body["refresh_token"])
    session = db.scalar(select(AuthSession))
    assert access["jti"] == refresh["jti"] == str(session.id)
    assert access["sub"] == str(db.scalar(select(User.id)))
    me = client.get("/users/me", headers=bearer(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "ana.google@example.com"


def test_second_google_sign_in_reuses_the_account(client, db, google):
    sign_in(client)

    response = sign_in(client)

    assert response.status_code == 200
    assert count(db, User) == 1
    assert count(db, AuthSession) == 2


def test_account_is_found_by_sub_even_if_google_email_changed(client, db, google):
    sign_in(client)
    google.identities["token-nuevo"] = GoogleIdentity(
        sub=ANA.sub, email="ana.nueva@example.com", email_verified=True
    )

    response = sign_in(client, "token-nuevo")

    assert response.status_code == 200
    assert count(db, User) == 1
    assert db.scalar(select(User.email)) == "ana.google@example.com"


def test_google_session_works_with_refresh_and_logout(client, google):
    tokens = sign_in(client).json()

    renewed = client.post("/users/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert renewed.status_code == 200
    logout = client.post("/users/logout", json={"refresh_token": renewed.json()["refresh_token"]})
    assert logout.status_code == 204


def test_deleted_google_account_starts_fresh_on_next_sign_in(client, db, google):
    tokens = sign_in(client).json()
    assert client.delete("/users/me", headers=bearer(tokens["access_token"])).status_code == 204

    response = sign_in(client)

    assert response.status_code == 201
    assert count(db, User) == 1


# --- Rechazos ------------------------------------------------------------------------------


def test_invalid_token_is_rejected_without_side_effects(client, db, google):
    response = sign_in(client, "token-falso")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_google_token"
    assert count(db, User) == count(db, AuthSession) == 0


@pytest.mark.parametrize(
    "identity",
    [
        GoogleIdentity(sub="s", email="ana@example.com", email_verified=False),
        GoogleIdentity(sub="s", email=None, email_verified=True),
        GoogleIdentity(sub="s", email="", email_verified=True),
    ],
)
def test_new_account_requires_a_verified_email(client, db, google, identity):
    google.identities["t"] = identity

    response = sign_in(client, "t")

    assert response.status_code == 401
    assert response.json()["code"] == "google_email_not_verified"
    assert count(db, User) == 0


def test_existing_google_account_signs_in_even_if_email_is_no_longer_verified(client, db, google):
    sign_in(client)
    google.identities["t"] = GoogleIdentity(sub=ANA.sub, email=None, email_verified=False)

    assert sign_in(client, "t").status_code == 200


def test_email_of_a_password_account_is_not_linked_automatically(client, db, google):
    client.post("/users", json={**CREDENTIALS, "email": "ana.google@example.com"})

    response = sign_in(client)

    assert response.status_code == 409
    assert response.json()["code"] == "google_account_conflict"
    user = db.scalar(select(User))
    assert user.google_sub is None
    assert count(db, User) == 1
    assert count(db, AuthSession) == 0


def test_email_of_another_google_account_is_a_conflict(client, db, google):
    sign_in(client)
    google.identities["otro"] = GoogleIdentity(
        sub="otro-sub", email="ana.google@example.com", email_verified=True
    )

    response = sign_in(client, "otro")

    assert response.status_code == 409
    assert count(db, User) == 1


def test_unconfigured_google_returns_503(client, db):
    app.dependency_overrides[get_google_verifier] = UnconfiguredGoogleVerifier

    response = sign_in(client)

    assert response.status_code == 503
    assert response.json()["code"] == "google_auth_unavailable"
    assert count(db, User) == 0


def test_google_keys_unreachable_returns_503(client, google):
    google.error = GoogleAuthUnavailable("sin red")

    response = sign_in(client)

    assert response.status_code == 503
    assert response.json()["code"] == "google_auth_unavailable"


def test_default_verifier_without_client_ids_is_unconfigured():
    get_google_verifier.cache_clear()
    try:
        assert isinstance(get_google_verifier(), UnconfiguredGoogleVerifier)
    finally:
        get_google_verifier.cache_clear()


@pytest.mark.parametrize("body", [{}, {"id_token": None}, {"token": "x"}, {"id_token": 123}])
def test_google_login_requires_an_id_token_string(client, google, body):
    assert client.post(GOOGLE_LOGIN, json=body).status_code == 422


def test_concurrent_creation_with_same_sub_signs_in_the_existing_account(db, monkeypatch):
    """Si otra petición crea la cuenta entre la búsqueda y la inserción, se reutiliza."""
    from app.modules.users import repository

    real_create = repository.create_google_user

    def create_twice(db_, email, sub):
        real_create(db_, email, sub)  # la otra petición gana
        return real_create(db_, email, sub)

    monkeypatch.setattr(repository, "create_google_user", create_twice)

    tokens, created = service.login_google(db, ANA)

    assert created is False
    assert tokens.access_token
    assert count(db, User) == 1


def test_google_login_is_documented_in_openapi(client):
    spec = client.get("/openapi.json").json()

    operation = spec["paths"][GOOGLE_LOGIN]["post"]
    schema_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert schema_ref.endswith("/GoogleAuthRequest")
    assert spec["components"]["schemas"]["GoogleAuthRequest"]["required"] == ["id_token"]
    assert {"200", "201", "401", "409", "422", "500", "503"} <= operation["responses"].keys()


# --- Cuentas solo de Google y contraseñas --------------------------------------------------


def test_google_sub_is_unique(db):
    db.add(User(email="a@example.com", google_sub="sub-1"))
    db.commit()
    db.add(User(email="b@example.com", google_sub="sub-1"))

    with pytest.raises(IntegrityError):
        db.commit()


def test_google_only_account_cannot_log_in_with_any_password(client, db, google):
    sign_in(client)

    for password in ["", "clave-segura-1", "lumio-dummy-password"]:
        response = client.post(
            "/users/login", json={"email": "ana.google@example.com", "password": password}
        )
        assert response.status_code == 401
    assert count(db, AuthSession) == 1


def test_registering_with_email_of_google_account_is_rejected(client, db, google):
    sign_in(client)

    response = client.post("/users", json={**CREDENTIALS, "email": "ana.google@example.com"})

    assert response.status_code == 409
    user = db.scalar(select(User))
    assert user.password_hash is None
    assert user.google_sub == ANA.sub


def test_google_only_account_cannot_change_password(client, google):
    tokens = sign_in(client).json()

    response = client.put(
        "/users/me/password",
        json={"current_password": "cualquiera-1", "new_password": "nueva-clave-1"},
        headers=bearer(tokens["access_token"]),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "password_not_set"
    assert client.get("/users/me", headers=bearer(tokens["access_token"])).status_code == 200
