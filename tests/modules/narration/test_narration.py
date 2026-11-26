"""SCRUM-38: piezas internas de la narración (texto, límite de uso, JPEG y Bedrock)."""

import uuid
from datetime import date

import pytest
from botocore.exceptions import ClientError, ReadTimeoutError

from app.core.config import Settings
from app.modules.narration.prompt import SYSTEM_PROMPT
from app.modules.narration.rate_limit import NarrationRateLimiter
from app.modules.narration.text import normalize_description
from app.modules.narration.vlm import (
    BedrockSceneDescriber,
    SceneDescriptionError,
    SceneDescriptionTimeout,
)
from app.modules.vision_orchestration.image import jpeg_size
from tests.modules.vision_orchestration.conftest import jpeg

# --- Texto -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Delante hay una puerta.", "Delante hay una puerta."),
        ("  delante hay una puerta  ", "delante hay una puerta."),
        ('"Hay un cruce a tu izquierda."', "Hay un cruce a tu izquierda."),
        ("- Hay escaleras.\n- Hay una rampa.", "Hay escaleras. Hay una rampa."),
        ("Uno. Dos. Tres.", "Uno. Dos."),
        ("**Letrero:** _Farmacia_", "Letrero: Farmacia."),
        ("   ", ""),
    ],
)
def test_normalize_description(raw, expected):
    assert normalize_description(raw) == expected


def test_normalize_caps_long_answers():
    text = normalize_description(" ".join(["palabra"] * 80))

    assert len(text.split()) <= 40
    assert text.endswith(".")


# --- Límite de uso -------------------------------------------------------------------


class Clock:
    def __init__(self) -> None:
        self.now = 0.0
        self.day = date(2026, 11, 25)


def test_rate_limit_min_interval_per_user():
    clock = Clock()
    limiter = NarrationRateLimiter(3, 100, clock=lambda: clock.now, today=lambda: clock.day)
    ana, beto = uuid.uuid4(), uuid.uuid4()

    assert limiter.try_acquire(ana)
    assert not limiter.try_acquire(ana)
    assert limiter.try_acquire(beto)
    clock.now = 3.0
    assert limiter.try_acquire(ana)


def test_rate_limit_daily_cap_resets_next_day():
    clock = Clock()
    limiter = NarrationRateLimiter(0, 2, clock=lambda: clock.now, today=lambda: clock.day)
    ana = uuid.uuid4()

    assert limiter.try_acquire(ana)
    assert limiter.try_acquire(ana)
    assert not limiter.try_acquire(ana)
    clock.day = date(2026, 11, 26)
    assert limiter.try_acquire(ana)


# --- JPEG --------------------------------------------------------------------------------


def test_jpeg_size_reads_the_header():
    assert jpeg_size(jpeg(width=576, height=768)) == (576, 768)


@pytest.mark.parametrize("data", [b"", b"\xff\xd8", b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff\xda\x00"])
def test_jpeg_size_rejects_invalid_data(data):
    assert jpeg_size(data) is None


# --- Configuración ---------------------------------------------------------------------


def test_fake_narration_only_in_local():
    with pytest.raises(ValueError):
        Settings(
            environment="dev",
            jwt_secret="x" * 40,
            narration_backend="fake",
        )


def test_default_model_is_us_inference_profile():
    settings = Settings()

    assert settings.narration_model_id.startswith("us.")
    assert settings.narration_backend == "disabled"


# --- Bedrock -----------------------------------------------------------------------------


class StubBedrock:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.requests: list[dict] = []

    def converse(self, **request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


def describer_with(stub: StubBedrock) -> BedrockSceneDescriber:
    describer = BedrockSceneDescriber("us.anthropic.claude-haiku-5-5", "us-east-1", 4.0)
    describer._client = stub
    return describer


def test_bedrock_request_follows_adr_308():
    stub = StubBedrock(
        response={
            "output": {"message": {"content": [{"text": "Delante hay una puerta."}]}},
            "usage": {"inputTokens": 850, "outputTokens": 12},
        }
    )
    image = jpeg()

    description = describer_with(stub).describe(image, language="es")

    assert description.text == "Delante hay una puerta."
    assert description.model == "us.anthropic.claude-haiku-5-5"
    request = stub.requests[0]
    assert request["modelId"] == "us.anthropic.claude-haiku-5-5"
    assert request["system"] == [{"text": SYSTEM_PROMPT}]
    assert request["inferenceConfig"] == {"temperature": 0.2, "maxTokens": 120}
    content = request["messages"][0]["content"]
    assert content[0] == {"image": {"format": "jpeg", "source": {"bytes": image}}}


def test_bedrock_client_error_is_unavailable():
    error = ClientError({"Error": {"Code": "ThrottlingException", "Message": "x"}}, "Converse")

    with pytest.raises(SceneDescriptionError) as raised:
        describer_with(StubBedrock(error=error)).describe(jpeg(), language="es")

    assert not isinstance(raised.value, SceneDescriptionTimeout)
    assert str(raised.value) == "ThrottlingException"


def test_bedrock_read_timeout_is_timeout():
    error = ReadTimeoutError(endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com")

    with pytest.raises(SceneDescriptionTimeout):
        describer_with(StubBedrock(error=error)).describe(jpeg(), language="es")


def test_prompt_forbids_what_adr_308_forbids():
    prompt = SYSTEM_PROMPT.lower()

    assert "30 palabras" in prompt
    assert "metros" in prompt
    assert "seguro" in prompt
    assert "identidad de las personas" in prompt
