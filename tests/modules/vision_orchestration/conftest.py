from datetime import UTC, datetime

import pytest

from app.main import app
from app.modules.narration.rate_limit import NarrationRateLimiter, get_rate_limiter
from app.modules.narration.vlm import SceneDescription, get_scene_describer

CREDENTIALS = {"email": "ana@example.com", "password": "clave-segura-1"}
CONSENT_VERSION = "2026-11-1"


def jpeg(width: int = 576, height: int = 768, padding: int = 0) -> bytes:
    """Encabezados de un JPEG baseline (SOI, APP0, SOF0, SOS) con el tamaño pedido.

    El backend solo lee los encabezados, así que no hace falta una imagen decodificable.
    """
    app0 = b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof0 = (
        b"\xff\xc0\x00\x11\x08"
        + height.to_bytes(2, "big")
        + width.to_bytes(2, "big")
        + b"\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01"
    )
    sos = b"\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00"
    return b"\xff\xd8" + app0 + sof0 + sos + b"\x00" * padding + b"\xff\xd9"


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def form(**overrides) -> dict:
    data = {
        "captured_at": datetime.now(UTC).isoformat(),
        "trigger": "gesture",
        "consent_version": CONSENT_VERSION,
    }
    data.update(overrides)
    return {key: value for key, value in data.items() if value is not None}


class FakeDescriber:
    """Guarda lo recibido. `error` se lanza en lugar de describir."""

    def __init__(self, text: str = "Delante hay un cruce peatonal con semáforo.") -> None:
        self.text = text
        self.calls: list[dict] = []
        self.error: Exception | None = None

    def describe(self, image: bytes, *, language: str) -> SceneDescription:
        self.calls.append({"bytes": len(image), "language": language})
        if self.error is not None:
            raise self.error
        return SceneDescription(text=self.text, model="modelo-de-prueba")


@pytest.fixture
def describer(client) -> FakeDescriber:
    fake = FakeDescriber()
    app.dependency_overrides[get_scene_describer] = lambda: fake
    return fake


@pytest.fixture
def limiter(client) -> NarrationRateLimiter:
    # Sin intervalo mínimo: cada prueba controla el límite que le interesa.
    instance = NarrationRateLimiter(min_interval_seconds=0, daily_limit=1000)
    app.dependency_overrides[get_rate_limiter] = lambda: instance
    return instance


@pytest.fixture
def token(client) -> str:
    client.post("/users", json=CREDENTIALS)
    return client.post("/users/login", json=CREDENTIALS).json()["access_token"]
