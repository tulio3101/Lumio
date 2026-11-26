"""VLM que describe la foto (SCRUM-263, ADR-308): Bedrock en dev y prod, texto fijo en local.

Nada de lo que pasa por aquí se guarda: la imagen solo vive en memoria durante la llamada y
los logs registran metadatos (modelo, bytes, tokens, latencia), nunca la imagen ni el texto.
"""

import logging
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Protocol

from fastapi import Depends

from app.core.config import get_settings
from app.modules.narration.prompt import SYSTEM_PROMPT, USER_TEXT

logger = logging.getLogger(__name__)


class SceneDescriptionError(Exception):
    """El VLM no respondió: throttling, error del servicio, modelo sin acceso o sin configurar."""


class SceneDescriptionTimeout(SceneDescriptionError):
    """El VLM tardó más que `NARRATION_TIMEOUT_SECONDS`."""


@dataclass(frozen=True)
class SceneDescription:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class SceneDescriber(Protocol):
    def describe(self, image: bytes, *, language: str) -> SceneDescription:
        """Describe la foto JPEG o lanza SceneDescriptionError."""


class UnconfiguredSceneDescriber:
    """NARRATION_BACKEND=disabled: la narración no está disponible y se dice con claridad."""

    def describe(self, image: bytes, *, language: str) -> SceneDescription:
        raise SceneDescriptionError("La narración no está configurada (NARRATION_BACKEND).")


class FakeSceneDescriber:
    """Solo en local: prueba la app de punta a punta sin AWS."""

    TEXT = "Descripción de prueba: delante hay un pasillo con una puerta a tu derecha."

    def describe(self, image: bytes, *, language: str) -> SceneDescription:
        return SceneDescription(text=self.TEXT, model="fake")


class BedrockSceneDescriber:
    """Converse API de Bedrock con el perfil de inferencia «us.» (ADR-308)."""

    def __init__(self, model_id: str, region: str, timeout_seconds: float) -> None:
        self._model_id = model_id
        self._region = region
        self._timeout = timeout_seconds
        self._client = None

    def _bedrock(self):  # noqa: ANN202 - el cliente de boto3 no tiene tipo estático
        if self._client is None:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self._region,
                config=Config(
                    # Sin reintentos: un segundo intento ya llegaría tarde para el usuario.
                    retries={"max_attempts": 1, "mode": "standard"},
                    connect_timeout=2,
                    read_timeout=self._timeout,
                ),
            )
        return self._client

    def describe(self, image: bytes, *, language: str) -> SceneDescription:
        from botocore.exceptions import (
            BotoCoreError,
            ClientError,
            ConnectTimeoutError,
            ReadTimeoutError,
        )

        started = time.perf_counter()
        try:
            response = self._bedrock().converse(
                modelId=self._model_id,
                system=[{"text": SYSTEM_PROMPT}],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"image": {"format": "jpeg", "source": {"bytes": image}}},
                            {"text": USER_TEXT},
                        ],
                    }
                ],
                inferenceConfig={"temperature": 0.2, "maxTokens": 120},
            )
        except (ReadTimeoutError, ConnectTimeoutError) as exc:
            raise SceneDescriptionTimeout(type(exc).__name__) from exc
        except ClientError as exc:
            # Solo el código de error: el mensaje de AWS puede repetir parte de la solicitud.
            raise SceneDescriptionError(exc.response.get("Error", {}).get("Code", "")) from exc
        except BotoCoreError as exc:
            raise SceneDescriptionError(type(exc).__name__) from exc

        usage = response.get("usage", {})
        logger.info(
            "Narración: modelo=%s bytes=%s tokens_in=%s tokens_out=%s latencia_ms=%s",
            self._model_id,
            len(image),
            usage.get("inputTokens"),
            usage.get("outputTokens"),
            round((time.perf_counter() - started) * 1000),
        )
        parts = response.get("output", {}).get("message", {}).get("content", [])
        text = " ".join(part["text"] for part in parts if "text" in part)
        return SceneDescription(
            text=text,
            model=self._model_id,
            input_tokens=usage.get("inputTokens"),
            output_tokens=usage.get("outputTokens"),
        )


@lru_cache
def get_scene_describer() -> SceneDescriber:
    settings = get_settings()
    if settings.narration_backend == "bedrock":
        return BedrockSceneDescriber(
            settings.narration_model_id, settings.aws_region, settings.narration_timeout_seconds
        )
    if settings.narration_backend == "fake":
        return FakeSceneDescriber()
    return UnconfiguredSceneDescriber()


SceneDescriberDep = Annotated[SceneDescriber, Depends(get_scene_describer)]
