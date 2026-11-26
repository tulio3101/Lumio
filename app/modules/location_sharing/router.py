import uuid
from typing import Any

from fastapi import APIRouter, Response, status
from fastapi.responses import HTMLResponse

from app.core.db import DbSession
from app.core.errors import ErrorResponse
from app.modules.location_sharing import service
from app.modules.location_sharing.schemas import LocationShareRead, LocationShareStart, Position
from app.modules.sos.email import EmailSenderDep
from app.modules.users.dependencies import CurrentUser

router = APIRouter(prefix="/location-shares", tags=["location-sharing"])

_AUTH: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Falta el access token o la sesión no es válida.",
    },
}
_OWNED: dict[int | str, dict[str, Any]] = {
    **_AUTH,
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "No existe o es de otra cuenta (`location_share_not_found`).",
    },
}
# La página la abre el contacto desde su correo: no se guarda en caché ni se indexa, y no
# filtra el enlace en el Referer al abrir el mapa.
_PAGE_HEADERS = {
    "Cache-Control": "no-store",
    "X-Robots-Tag": "noindex, nofollow",
    "Referrer-Policy": "no-referrer",
}


@router.post(
    "",
    response_model=LocationShareRead,
    status_code=status.HTTP_201_CREATED,
    summary="Empezar a compartir la ubicación",
    description=(
        "Envía a cada contacto de confianza un correo con un enlace privado a la ubicación "
        "actual. Dura `duration_minutes` como máximo (15–240) o hasta detenerlo. Empezar otro "
        "cierra el anterior. Solo se guarda la última posición."
    ),
    responses={
        **_AUTH,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "No hay contactos de confianza (`no_trusted_contacts`).",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorResponse,
            "description": (
                "El correo no llegó a ningún contacto (`location_share_delivery_failed`)."
            ),
        },
    },
)
def start_sharing(
    payload: LocationShareStart, user: CurrentUser, db: DbSession, sender: EmailSenderDep
) -> LocationShareRead:
    share = service.start(db, user, payload, sender, service.utcnow())
    return LocationShareRead(
        id=share.id,
        expires_at=share.expires_at,
        contacts_total=share.contacts_total,
        contacts_sent=share.contacts_sent,
    )


@router.put(
    "/{share_id}/position",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Actualizar la posición compartida",
    responses={
        **_OWNED,
        status.HTTP_410_GONE: {
            "model": ErrorResponse,
            "description": "Ya se detuvo o venció (`location_share_ended`).",
        },
    },
)
def update_position(
    share_id: uuid.UUID, position: Position, user: CurrentUser, db: DbSession
) -> Response:
    service.update_position(db, user, share_id, position, service.utcnow())
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Dejar de compartir la ubicación",
    description="Termina y borra la posición. Repetirlo no hace nada.",
    responses=_OWNED,
)
def stop_sharing(share_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    service.stop(db, user, share_id, service.utcnow())
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/view/{token}",
    response_class=HTMLResponse,
    summary="Página de la ubicación compartida (para los contactos)",
    description="Sin sesión: el token del enlace es la autorización. 404 si no existe.",
    include_in_schema=True,
)
def view_share(token: str, db: DbSession) -> HTMLResponse:
    html = service.page_for_token(db, token, service.utcnow())
    if html is None:
        return HTMLResponse(
            "<!doctype html><html lang='es'><meta charset='utf-8'>"
            "<meta name='robots' content='noindex'><p>Este enlace no existe.</p></html>",
            status_code=status.HTTP_404_NOT_FOUND,
            headers=_PAGE_HEADERS,
        )
    return HTMLResponse(html, headers=_PAGE_HEADERS)
