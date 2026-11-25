from fastapi import status

from app.core.errors import AppError


class NoTrustedContactsError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "no_trusted_contacts"
    message = (
        "No tienes contactos de confianza, así que no se envió la alerta. "
        "Agrega al menos uno en Preferencias."
    )


class SosDeliveryError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "sos_delivery_failed"
    message = "No se pudo enviar la alerta a ninguno de tus contactos. Intenta de nuevo."


class SosRecordError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "sos_record_failed"
    message = "No se pudo registrar la alerta, así que no se envió. Intenta de nuevo."
