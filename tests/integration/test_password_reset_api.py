"""Recuperar Contraseña contra Postgres: migración 0009 y borrado en cascada."""

import re

from sqlalchemy import select

from app.main import app
from app.modules.sos.email import get_email_sender
from app.modules.users.models import PasswordResetCode
from tests.modules.sos.conftest import FakeEmailSender

from .conftest import PASSWORD

NEW_PASSWORD = "otra-clave-segura"


def use_fake_mail() -> FakeEmailSender:
    sender = FakeEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: sender
    return sender


def test_password_can_be_reset_with_the_emailed_code(api, session_factory, user, auth):
    mail = use_fake_mail()

    assert api.post("/users/password-reset", json={"email": user.email}).status_code == 202
    code = re.search(r"Tu código es: (\d{6})", mail.sent[-1]["body"]).group(1)
    response = api.post(
        "/users/password-reset/confirm",
        json={"email": user.email, "code": code, "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 204
    assert api.get("/users/me", headers=auth).status_code == 401
    old = api.post("/users/login", json={"email": user.email, "password": PASSWORD})
    new = api.post("/users/login", json={"email": user.email, "password": NEW_PASSWORD})
    assert (old.status_code, new.status_code) == (401, 200)
    with session_factory() as session:
        assert session.scalar(select(PasswordResetCode)) is None


def test_deleting_the_account_deletes_its_reset_codes(api, session_factory, user, auth):
    use_fake_mail()
    api.post("/users/password-reset", json={"email": user.email})

    assert api.delete("/users/me", headers=auth).status_code == 204

    with session_factory() as session:
        assert session.scalar(select(PasswordResetCode)) is None
