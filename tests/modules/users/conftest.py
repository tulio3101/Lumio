import pytest

CREDENTIALS = {"email": "ana@example.com", "password": "clave-segura-1"}


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tokens(client) -> dict:
    """Registra a Ana e inicia sesión; devuelve el TokenPair."""
    client.post("/users", json=CREDENTIALS)
    return client.post("/users/login", json=CREDENTIALS).json()
