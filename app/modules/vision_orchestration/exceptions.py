from fastapi import status

from app.core.errors import AppError


class ConsentRequiredError(AppError):
    """SCRUM-324 / ADR-308: sin consentimiento vigente no se procesa ninguna imagen."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "consent_required"
    message = "El usuario no ha dado su consentimiento para enviar imágenes."
