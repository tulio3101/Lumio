"""Narración del entorno (SCRUM-38): valida la foto, la describe con el VLM y la descarta.

Orden de las comprobaciones: consentimiento (no se mira la foto sin él), límite de uso, foto
y VLM. La foto vive solo en memoria durante la solicitud; nunca se escribe en disco, base de
datos ni logs.
"""

import logging
import time
import uuid

from app.modules.narration.availability import NarrationAvailability
from app.modules.narration.rate_limit import NarrationRateLimiter
from app.modules.narration.text import normalize_description
from app.modules.narration.vlm import (
    SceneDescriber,
    SceneDescriptionError,
    SceneDescriptionTimeout,
    UnconfiguredSceneDescriber,
)
from app.modules.vision_orchestration.exceptions import (
    ConsentRequiredError,
    ImageTooLargeError,
    InvalidImageError,
    NarrationRateLimitedError,
    NarrationTimeoutError,
    NarrationUnavailableError,
)
from app.modules.vision_orchestration.image import MAX_IMAGE_BYTES, MAX_LONG_SIDE_PX, jpeg_size
from app.modules.vision_orchestration.schemas import (
    NarrationStatusReason,
    NarrationStatusResponse,
    NarrationTrigger,
    SceneLanguage,
    VisionAnalysisResponse,
)

logger = logging.getLogger(__name__)


def narration_status(
    describer: SceneDescriber, availability: NarrationAvailability
) -> NarrationStatusResponse:
    """SCRUM-41: si conviene enviar fotos ahora. No llama al VLM ni gasta cupo."""
    if isinstance(describer, UnconfiguredSceneDescriber):
        return NarrationStatusResponse(available=False, reason=NarrationStatusReason.NOT_CONFIGURED)
    snapshot = availability.snapshot()
    if snapshot.degraded:
        return NarrationStatusResponse(
            available=False,
            reason=NarrationStatusReason.DEGRADED,
            retry_after_seconds=snapshot.retry_after_seconds,
        )
    return NarrationStatusResponse(available=True, reason=NarrationStatusReason.AVAILABLE)


def _record_failure(availability: NarrationAvailability | None) -> None:
    if availability is not None:
        availability.record_failure()


def require_consent(consent_version: str | None) -> None:
    if not consent_version or not consent_version.strip():
        raise ConsentRequiredError()


def validate_image(image: bytes) -> None:
    if len(image) > MAX_IMAGE_BYTES:
        raise ImageTooLargeError()
    size = jpeg_size(image)
    if size is None:
        raise InvalidImageError()
    if max(size) > MAX_LONG_SIDE_PX:
        raise ImageTooLargeError()


def describe_scene(
    *,
    user_id: uuid.UUID,
    image: bytes,
    trigger: NarrationTrigger,
    language: SceneLanguage,
    describer: SceneDescriber,
    limiter: NarrationRateLimiter,
    availability: NarrationAvailability | None = None,
) -> VisionAnalysisResponse:
    validate_image(image)
    if not limiter.try_acquire(user_id, trigger):
        raise NarrationRateLimitedError()

    started = time.perf_counter()
    try:
        description = describer.describe(image, language=language.value)
    except SceneDescriptionTimeout as exc:
        logger.warning("Narración: el VLM tardó demasiado (%s)", exc)
        _record_failure(availability)
        raise NarrationTimeoutError() from exc
    except SceneDescriptionError as exc:
        logger.warning("Narración no disponible: %s", exc)
        _record_failure(availability)
        raise NarrationUnavailableError() from exc
    latency_ms = round((time.perf_counter() - started) * 1000)

    text = normalize_description(description.text)
    if not text:
        # Una respuesta vacía no se locuta: para la app es lo mismo que no tener narración.
        logger.warning("Narración: el VLM %s respondió sin texto", description.model)
        _record_failure(availability)
        raise NarrationUnavailableError()
    if availability is not None:
        availability.record_success()

    logger.info(
        "Narración servida: disparo=%s modelo=%s bytes=%s latencia_ms=%s",
        trigger.value,
        description.model,
        len(image),
        latency_ms,
    )
    return VisionAnalysisResponse(text=text, model=description.model, latency_ms=latency_ms)
