"""Correo y página de la ubicación compartida. El correo es texto plano y la página escapa
todo lo que viene de la cuenta: nada del cliente se interpreta como marcado."""

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from app.modules.sos.message import Location, map_link, sender_label

# Como en el correo de emergencia: los usuarios y sus contactos están en Colombia.
_TIMEZONE = ZoneInfo("America/Bogota")


def _local(value: datetime) -> str:
    return value.astimezone(_TIMEZONE).strftime("%Y-%m-%d %H:%M")


def subject(display_name: str | None, email: str) -> str:
    return f"{display_name or email} comparte su ubicación contigo"


def body(*, display_name: str | None, email: str, link: str, expires_at: datetime) -> str:
    return (
        f"{sender_label(display_name, email)} empezó a compartir su ubicación contigo desde "
        "Lumio porque te eligió como contacto de confianza.\n\n"
        f"Ver su ubicación actual: {link}\n\n"
        f"El enlace funciona hasta las {_local(expires_at)} (hora de Colombia) o hasta que "
        "deje de compartirla. Muestra solo la última posición, no un historial.\n\n"
        "No reenvíes este enlace: quien lo tenga puede ver la ubicación mientras esté activo. "
        "Este correo es automático: no respondas a este mensaje.\n"
    )


_PAGE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
{refresh}
<title>Ubicación compartida · Lumio</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; max-width: 34rem; margin: 2rem auto;
       padding: 0 1rem; line-height: 1.5; color: #1b1b1f; }}
a.button {{ display: inline-block; padding: .8rem 1.2rem; border-radius: .6rem;
           background: #1f5fbf; color: #fff; text-decoration: none; font-weight: 600; }}
.muted {{ color: #55575f; }}
</style>
</head>
<body>
<main>
<h1>{heading}</h1>
{content}
<p class="muted">Lumio · Este enlace es privado: no lo reenvíes.</p>
</main>
</body>
</html>
"""


def page(
    *,
    display_name: str | None,
    email: str,
    location: Location | None,
    updated_at: datetime | None,
    expires_at: datetime,
    active: bool,
) -> str:
    who = escape(display_name or email)
    if not active:
        return _PAGE.format(
            refresh="",
            heading=f"{who} ya no comparte su ubicación",
            content=(
                "<p>El uso compartido terminó. Si te preocupa, comunícate con esta persona.</p>"
            ),
        )
    if location is None or updated_at is None:
        content = "<p>Todavía no hay una posición. Esta página se actualiza sola.</p>"
    else:
        accuracy = (
            f" (precisión aproximada: {round(location.accuracy_m)} metros)"
            if location.accuracy_m is not None
            else ""
        )
        content = (
            f"<p>Última posición recibida: {escape(_local(updated_at))} (hora de Colombia)"
            f"{escape(accuracy)}.</p>"
            f'<p><a class="button" href="{escape(map_link(location))}" rel="noreferrer">'
            "Ver en el mapa</a></p>"
        )
    content += (
        f'<p class="muted">Se comparte hasta las {escape(_local(expires_at))}. '
        "La página se actualiza cada 30 segundos.</p>"
    )
    return _PAGE.format(
        refresh='<meta http-equiv="refresh" content="30">',
        heading=f"Ubicación de {who}",
        content=content,
    )
