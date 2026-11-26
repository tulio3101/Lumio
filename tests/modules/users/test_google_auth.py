"""Verificación real del ID token de Google, con llaves RSA propias y sin red.

Se firman tokens como lo haría Google y se sirven las llaves públicas con un transporte
falso en lugar de https://www.googleapis.com/oauth2/v1/certs.
"""

import json
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from google.auth import crypt, jwt

from app.core.config import Settings
from app.modules.users.google_auth import (
    GoogleAuthUnavailable,
    GoogleIdTokenVerifier,
    InvalidGoogleToken,
)

CLIENT_ID = "lumio-ios.apps.googleusercontent.com"
KEY_ID = "llave-1"


def _keypair() -> tuple[bytes, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private, public


GOOGLE_PRIVATE, GOOGLE_PUBLIC = _keypair()
OTHER_PRIVATE, _ = _keypair()


class FakeResponse:
    def __init__(self, status: int, data: bytes) -> None:
        self.status = status
        self.data = data
        self.headers = {}


class FakeCertsRequest:
    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.calls = 0

    def __call__(self, url, method="GET", **kwargs):
        self.calls += 1
        return FakeResponse(self.status, json.dumps({KEY_ID: GOOGLE_PUBLIC.decode()}).encode())


def make_token(private_key: bytes = GOOGLE_PRIVATE, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "1234567890",
        "email": "ana@gmail.com",
        "email_verified": True,
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    signer = crypt.RSASigner.from_string(private_key, key_id=KEY_ID)
    return jwt.encode(signer, claims).decode()


@pytest.fixture
def certs() -> FakeCertsRequest:
    return FakeCertsRequest()


@pytest.fixture
def verifier(certs) -> GoogleIdTokenVerifier:
    verifier = GoogleIdTokenVerifier([CLIENT_ID, "lumio-web.apps.googleusercontent.com"])
    verifier._request = certs
    return verifier


def test_valid_token_returns_identity(verifier, certs):
    identity = verifier.verify(make_token())

    assert identity.sub == "1234567890"
    assert identity.email == "ana@gmail.com"
    assert identity.email_verified is True
    assert certs.calls == 1


def test_accepts_any_configured_client_id_and_both_issuer_forms(verifier):
    token = make_token(aud="lumio-web.apps.googleusercontent.com", iss="accounts.google.com")

    assert verifier.verify(token).sub == "1234567890"


@pytest.mark.parametrize(("value", "expected"), [("true", True), ("false", False), (None, False)])
def test_email_verified_accepts_string_form(verifier, value, expected):
    assert verifier.verify(make_token(email_verified=value)).email_verified is expected


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(make_token(aud="otra-app.apps.googleusercontent.com"), id="otra-audiencia"),
        pytest.param(make_token(iss="https://evil.example.com"), id="otro-emisor"),
        pytest.param(
            make_token(iat=int(time.time()) - 7200, exp=int(time.time()) - 3600), id="vencido"
        ),
        pytest.param(make_token(OTHER_PRIVATE), id="firmado-con-otra-llave"),
        pytest.param(make_token(sub=""), id="sin-sub"),
        pytest.param("no-es-un-jwt", id="basura"),
        pytest.param(make_token()[:-4] + "AAAA", id="firma-alterada"),
    ],
)
def test_invalid_tokens_are_rejected(verifier, token):
    with pytest.raises(InvalidGoogleToken):
        verifier.verify(token)


def test_unsigned_token_is_rejected(verifier):
    header, payload, _ = make_token().split(".")
    with pytest.raises(InvalidGoogleToken):
        verifier.verify(f"{header}.{payload}.")


def test_certs_unreachable_means_unavailable_not_invalid(certs, verifier):
    certs.status = 500

    with pytest.raises(GoogleAuthUnavailable):
        verifier.verify(make_token())


def test_client_ids_are_read_comma_separated(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_IDS", " ios.apps.googleusercontent.com , web.apps , ")

    settings = Settings(_env_file=None)

    assert settings.google_client_ids == ["ios.apps.googleusercontent.com", "web.apps"]


def test_client_ids_default_to_empty():
    assert Settings(_env_file=None).google_client_ids == []
