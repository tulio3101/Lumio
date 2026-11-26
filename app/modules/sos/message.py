"""Texto del correo de emergencia. Solo texto plano: lo escribe el sistema, nada del
cliente se interpreta como marcado."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

# Los usuarios y sus contactos están en Colombia (celular colombiano en el perfil).
_TIMEZONE = ZoneInfo("America/Bogota")
# Línea única de emergencias de Colombia.
EMERGENCY_LINE = "123"


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    accuracy_m: float | None


def sender_label(display_name: str | None, email: str) -> str:
    """Quién envía la alerta: el nombre si lo puso, y siempre el correo de la cuenta."""
    return f"{display_name} ({email})" if display_name else email


def subject(display_name: str | None, email: str) -> str:
    return f"ALERTA DE EMERGENCIA: {display_name or email} necesita ayuda"


def map_link(location: Location) -> str:
    return f"https://www.google.com/maps?q={location.latitude:.6f},{location.longitude:.6f}"


def body(
    *, display_name: str | None, email: str, sent_at: datetime, location: Location | None
) -> str:
    when = sent_at.astimezone(_TIMEZONE).strftime("%Y-%m-%d %H:%M")
    if location is None:
        where = (
            "No se pudo obtener su ubicación (el teléfono no tenía permiso de ubicación o "
            "señal GPS). Intenta comunicarte con esta persona por otro medio."
        )
    else:
        where = f"Ubicación: {map_link(location)}"
        if location.accuracy_m is not None:
            where += f"\nPrecisión aproximada: {round(location.accuracy_m)} metros."
    return (
        "ALERTA DE EMERGENCIA\n\n"
        f"{sender_label(display_name, email)} activó el botón de emergencia de Lumio y te "
        "eligió como contacto de confianza.\n\n"
        f"Hora: {when} (hora de Colombia)\n"
        f"{where}\n\n"
        "Qué hacer: intenta comunicarte con esta persona. Si crees que está en peligro, "
        f"llama a la línea de emergencias {EMERGENCY_LINE}.\n\n"
        "Lumio no sustituye a los servicios de emergencia. Este correo es automático: "
        "no respondas a este mensaje.\n"
    )
