from datetime import timedelta

import jwt
import pytest

from app.core.security import create_token, decode_token, hash_password, verify_password


def test_hash_password_is_not_plaintext_and_verifies():
    password_hash = hash_password("secreto-123")

    assert password_hash != "secreto-123"
    assert verify_password("secreto-123", password_hash)


def test_verify_password_rejects_wrong_password_and_invalid_hash():
    password_hash = hash_password("secreto-123")

    assert not verify_password("otra-clave", password_hash)
    assert not verify_password("secreto-123", "no-es-un-hash")


def test_token_roundtrip_keeps_claims():
    token = create_token("user-1", "access", timedelta(minutes=5), jti="sesion-1")

    claims = decode_token(token)

    assert claims["sub"] == "user-1"
    assert claims["type"] == "access"
    assert claims["jti"] == "sesion-1"


def test_token_without_jti_has_no_jti_claim():
    claims = decode_token(create_token("user-1", "access", timedelta(minutes=5)))

    assert "jti" not in claims


def test_decode_token_rejects_expired_token():
    token = create_token("user-1", "access", timedelta(seconds=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


def test_decode_token_rejects_tampered_token():
    token = create_token("user-1", "access", timedelta(minutes=5))

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token[:-2] + "xx")
