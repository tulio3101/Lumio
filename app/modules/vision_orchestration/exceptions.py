from fastapi import status

from app.core.errors import AppError


class ConsentRequiredError(AppError):
    """SCRUM-324 / ADR-308: sin consentimiento vigente no se procesa ninguna imagen."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "consent_required"
    message = "El usuario no ha dado su consentimiento para enviar imágenes."


class ImageTooLargeError(AppError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    code = "image_too_large"
    message = "La foto es demasiado grande: máximo 1 MB y 1024 píxeles de lado largo."


class InvalidImageError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "invalid_image"
    message = "La foto no es un JPEG válido."


class NarrationRateLimitedError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "narration_rate_limited"
    message = "Demasiadas solicitudes de narración. Espera unos segundos e inténtalo de nuevo."


class NarrationUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "narration_unavailable"
    message = "La narración del entorno no está disponible en este momento."


class NarrationTimeoutError(AppError):
    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    code = "narration_timeout"
    message = "La descripción tardó demasiado. Inténtalo de nuevo."
