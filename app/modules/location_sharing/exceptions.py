from fastapi import status

from app.core.errors import AppError


class NoTrustedContactsError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "no_trusted_contacts"
    message = "No tienes contactos de confianza con quienes compartir tu ubicación."


class LocationShareNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "location_share_not_found"
    message = "No se encontró ese uso compartido de la ubicación."


class LocationShareEndedError(AppError):
    status_code = status.HTTP_410_GONE
    code = "location_share_ended"
    message = "Ese uso compartido de la ubicación ya terminó."


class LocationShareDeliveryError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "location_share_delivery_failed"
    message = "No se pudo avisar a ningún contacto. No se está compartiendo la ubicación."
