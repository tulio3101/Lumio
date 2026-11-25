import pytest

CREDENTIALS = {"email": "ana@example.com", "password": "clave-segura-1"}
MARIA = {"name": "María Gómez", "email": "maria@example.com"}


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def sign_in(client, credentials: dict) -> str:
    """Registra la cuenta, inicia sesión y devuelve el access token."""
    client.post("/users", json=credentials)
    return client.post("/users/login", json=credentials).json()["access_token"]


@pytest.fixture
def token(client) -> str:
    return sign_in(client, CREDENTIALS)


@pytest.fixture
def luis_token(client) -> str:
    return sign_in(client, {"email": "luis@example.com", "password": "clave-segura-2"})
