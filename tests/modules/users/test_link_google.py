"""Asociar una cuenta de Google a la cuenta de Lumio con sesión iniciada (SCRUM-62).

Una cuenta creada con correo y contraseña no se une sola a Google (409
google_account_conflict en /users/login/google). Con la sesión iniciada, POST
/users/me/google la asocia y desde entonces se puede entrar con Google o con la contraseña.
"""

import pytest
from sqlalchemy import func, select

from app.main import app
from app.modules.users.google_auth import (
    GoogleAuthUnavailable,
    GoogleIdentity,
    UnconfiguredGoogleVerifier,
    get_google_verifier,
)
from app.modules.users.models import AuthSession, User

from .conftest import CREDENTIALS, bearer
from .test_login_google import ANA, GOOGLE_LOGIN, FakeVerifier

LINK = "/users/me/google"


@pytest.fixture
def google(client) -> FakeVerifier:
    verifier = FakeVerifier()
    app.dependency_overrides[get_google_verifier] = lambda: verifier
    return verifier


def link(client, tokens: dict, id_token: str = "token-ana"):
    return client.post(
        LINK, json={"id_token": id_token}, headers=bearer(tokens["access_token"])
    )


def test_password_account_links_google_and_then_signs_in_with_it(client, db, google, tokens):
    response = link(client, tokens)

    assert response.status_code == 200
    assert response.json()["google_linked"] is True
    assert response.json()["email"] == CREDENTIALS["email"]
    user = db.scalar(select(User))
    assert user.google_sub == ANA.sub
    assert user.password_hash is not None

    google_login = client.post(GOOGLE_LOGIN, json={"id_token": "token-ana"})
    assert google_login.status_code == 200
    assert db.scalar(select(func.count()).select_from(User)) == 1
    password_login = client.post("/users/login", json=CREDENTIALS)
    assert password_login.status_code == 200


def test_linking_resolves_the_email_conflict(client, db, google):
    """El caso del 409: mismo correo en Google y en una cuenta con contraseña."""
    client.post("/users", json={**CREDENTIALS, "email": "ana.google@example.com"})
    assert client.post(GOOGLE_LOGIN, json={"id_token": "token-ana"}).status_code == 409
    tokens = client.post(
        "/users/login", json={**CREDENTIALS, "email": "ana.google@example.com"}
    ).json()

    assert link(client, tokens).status_code == 200
    assert client.post(GOOGLE_LOGIN, json={"id_token": "token-ana"}).status_code == 200


def test_me_reports_whether_google_is_linked(client, google, tokens):
    headers = bearer(tokens["access_token"])
    assert client.get("/users/me", headers=headers).json()["google_linked"] is False

    link(client, tokens)

    assert client.get("/users/me", headers=headers).json()["google_linked"] is True


def test_google_only_account_reports_google_linked(client, google):
    body = client.post(GOOGLE_LOGIN, json={"id_token": "token-ana"}).json()

    me = client.get("/users/me", headers=bearer(body["access_token"]))

    assert me.json()["google_linked"] is True


def test_linking_the_same_google_account_twice_changes_nothing(client, db, google, tokens):
    link(client, tokens)

    response = link(client, tokens)

    assert response.status_code == 200
    assert db.scalar(select(User.google_sub)) == ANA.sub


def test_account_with_another_google_account_is_a_conflict(client, db, google, tokens):
    link(client, tokens)
    google.identities["otra"] = GoogleIdentity(
        sub="otro-sub", email="otra@example.com", email_verified=True
    )

    response = link(client, tokens, "otra")

    assert response.status_code == 409
    assert response.json()["code"] == "google_already_linked"
    assert db.scalar(select(User.google_sub)) == ANA.sub


def test_google_account_of_another_lumio_account_is_a_conflict(client, db, google, tokens):
    client.post(GOOGLE_LOGIN, json={"id_token": "token-ana"})  # cuenta solo de Google

    response = link(client, tokens)

    assert response.status_code == 409
    assert response.json()["code"] == "google_account_in_use"
    password_user = db.scalar(select(User).where(User.email == CREDENTIALS["email"]))
    assert password_user.google_sub is None


def test_email_does_not_need_to_match(client, db, google, tokens):
    google.identities["t"] = GoogleIdentity(
        sub="sub-distinto", email="otro.correo@example.com", email_verified=False
    )

    assert link(client, tokens, "t").status_code == 200
    assert db.scalar(select(User.email)) == CREDENTIALS["email"]


def test_invalid_google_token_is_403_so_the_session_is_not_renewed(client, db, google, tokens):
    response = link(client, tokens, "token-falso")

    assert response.status_code == 403
    assert response.json()["code"] == "invalid_google_token"
    assert db.scalar(select(User.google_sub)) is None


def test_linking_requires_a_session(client, db, google):
    response = client.post(LINK, json={"id_token": "token-ana"})

    assert response.status_code == 401
    assert db.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_unconfigured_google_returns_503(client, tokens):
    app.dependency_overrides[get_google_verifier] = UnconfiguredGoogleVerifier

    response = link(client, tokens)

    assert response.status_code == 503
    assert response.json()["code"] == "google_auth_unavailable"


def test_google_keys_unreachable_returns_503(client, google, tokens):
    google.error = GoogleAuthUnavailable("sin red")

    assert link(client, tokens).status_code == 503


def test_link_is_documented_in_openapi(client):
    spec = client.get("/openapi.json").json()

    operation = spec["paths"][LINK]["post"]
    assert {"200", "401", "403", "409", "500", "503"} <= operation["responses"].keys()
    assert "google_linked" in spec["components"]["schemas"]["UserRead"]["properties"]
