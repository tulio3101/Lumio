"""Recuperar Contraseña: código por correo, sin revelar si la cuenta existe."""

import re
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.main import app
from app.modules.sos.email import get_email_sender
from app.modules.users import password_reset
from app.modules.users.models import PasswordResetCode, User
from tests.modules.sos.conftest import FakeEmailSender

from .conftest import CREDENTIALS, bearer

NEW_PASSWORD = "otra-clave-segura"
ACCEPTED = {
    "message": (
        "Si el correo corresponde a una cuenta con contraseña, te enviamos un código. "
        "Revisa tu correo."
    )
}


@pytest.fixture
def mail(client) -> FakeEmailSender:
    sender = FakeEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: sender
    return sender


def code_in(mail: FakeEmailSender) -> str:
    match = re.search(r"Tu código es: (\d{6})", mail.sent[-1]["body"])
    assert match
    return match.group(1)


def request_code(client, email=CREDENTIALS["email"]):
    return client.post("/users/password-reset", json={"email": email})


def confirm(client, code, password=NEW_PASSWORD, email=CREDENTIALS["email"]):
    return client.post(
        "/users/password-reset/confirm",
        json={"email": email, "code": code, "new_password": password},
    )


def wrong(code: str) -> str:
    return f"{(int(code) + 1) % 1_000_000:06d}"


# Pedir el código


def test_own_account_receives_a_code_by_email(client, db, tokens, mail):
    response = request_code(client, " ANA@example.com ")

    assert (response.status_code, response.json()) == (202, ACCEPTED)
    assert mail.recipients == ["ana@example.com"]
    code = code_in(mail)
    assert " ".join(code) in mail.sent[-1]["body"]
    stored = db.scalar(select(PasswordResetCode))
    assert stored.code_hash != code
    assert stored.attempts == 0


def test_unknown_email_gets_the_same_answer_and_no_email(client, mail):
    response = request_code(client, "nadie@example.com")

    assert (response.status_code, response.json()) == (202, ACCEPTED)
    assert mail.sent == []


def test_google_only_accounts_do_not_receive_a_code(client, db, mail):
    db.add(User(email="google@example.com", password_hash=None, google_sub="sub-1"))
    db.commit()

    response = request_code(client, "google@example.com")

    assert (response.status_code, response.json()) == (202, ACCEPTED)
    assert mail.sent == []


def test_a_second_request_within_a_minute_sends_nothing(client, tokens, mail):
    request_code(client)
    response = request_code(client)

    assert response.status_code == 202
    assert len(mail.sent) == 1


def test_failed_delivery_is_not_revealed(client, tokens, mail):
    mail.fail_all = True

    response = request_code(client)

    assert (response.status_code, response.json()) == (202, ACCEPTED)


# Restablecer


def test_the_code_sets_a_new_password_and_closes_every_session(client, db, tokens, mail):
    request_code(client)

    response = confirm(client, code_in(mail))

    assert response.status_code == 204
    old = client.post("/users/login", json=CREDENTIALS)
    new = client.post("/users/login", json={**CREDENTIALS, "password": NEW_PASSWORD})
    assert (old.status_code, new.status_code) == (401, 200)
    assert client.get("/users/me", headers=bearer(tokens["access_token"])).status_code == 401
    assert db.scalar(select(PasswordResetCode)) is None


def test_a_code_works_only_once(client, tokens, mail):
    request_code(client)
    code = code_in(mail)
    confirm(client, code)

    response = confirm(client, code, password="tercera-clave")

    assert (response.status_code, response.json()["code"]) == (400, "invalid_reset_code")


def test_a_wrong_code_is_rejected_and_counted(client, db, tokens, mail):
    request_code(client)

    response = confirm(client, wrong(code_in(mail)))

    assert (response.status_code, response.json()["code"]) == (400, "invalid_reset_code")
    assert db.scalar(select(PasswordResetCode)).attempts == 1
    assert client.post("/users/login", json=CREDENTIALS).status_code == 200


def test_after_five_wrong_codes_the_right_one_no_longer_works(client, tokens, mail):
    request_code(client)
    code = code_in(mail)
    for _ in range(password_reset.RESET_CODE_MAX_ATTEMPTS):
        confirm(client, wrong(code))

    assert confirm(client, code).status_code == 400


def test_an_expired_code_is_rejected(client, db, tokens, mail):
    request_code(client)
    stored = db.scalar(select(PasswordResetCode))
    stored.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    assert confirm(client, code_in(mail)).status_code == 400


def test_only_the_latest_code_is_valid(client, db, tokens, mail):
    request_code(client)
    first = code_in(mail)
    # Simula que pasó el minuto de espera.
    stored = db.scalar(select(PasswordResetCode))
    stored.created_at = datetime.now(UTC) - timedelta(minutes=2)
    db.commit()
    request_code(client)
    latest = code_in(mail)

    if first != latest:
        assert confirm(client, first).status_code == 400
    assert confirm(client, latest).status_code == 204


def test_unknown_email_cannot_confirm(client, mail):
    response = confirm(client, "123456", email="nadie@example.com")

    assert (response.status_code, response.json()["code"]) == (400, "invalid_reset_code")


@pytest.mark.parametrize(
    "body",
    [
        {"email": "ana@example.com", "code": "123456", "new_password": "corta"},
        {"email": "ana@example.com", "code": "12345", "new_password": NEW_PASSWORD},
        {"email": "ana@example.com", "code": "abcdef", "new_password": NEW_PASSWORD},
        {"email": "no-es-correo", "code": "123456", "new_password": NEW_PASSWORD},
    ],
)
def test_invalid_requests_are_rejected(client, tokens, body):
    assert client.post("/users/password-reset/confirm", json=body).status_code == 422


def test_message_reads_the_code_digit_by_digit():
    subject, body = password_reset.message("482915")

    assert "Lumio" in subject
    assert "Tu código es: 482915" in body
    assert "4 8 2 9 1 5" in body
    assert "15 minutos" in body
