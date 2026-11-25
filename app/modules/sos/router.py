from typing import Any

from fastapi import APIRouter, Response, status

from app.core.db import DbSession
from app.core.errors import ErrorResponse
from app.modules.sos import service
from app.modules.sos.email import EmailSenderDep
from app.modules.sos.schemas import SosRead, SosRequest
from app.modules.users.dependencies import CurrentUser

router = APIRouter(prefix="/sos", tags=["sos"])

_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Falta el access token o la sesión no es válida.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "No hay contactos de confianza (`no_trusted_contacts`); no se envió nada.",
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponse,
        "description": "No se pudo registrar la alerta (`sos_record_failed`).",
    },
    status.HTTP_502_BAD_GATEWAY: {
        "model": ErrorResponse,
        "description": "El correo no salió a ningún contacto (`sos_delivery_failed`).",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "Persistencia no disponible; no se envió nada.",
    },
}


@router.post(
    "",
    response_model=SosRead,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar alerta de emergencia",
    description=(
        "Envía un correo a cada contacto de confianza del usuario con su ubicación (si la "
        "app la tiene), quién lo envía y que es una alerta de emergencia. Sin ubicación se "
        "envía igual, avisando que falta. Es idempotente por `idempotency_key`: repetir una "
        "alerta ya entregada responde 200 con la misma alerta y no envía correos otra vez; "
        "una que falló se reintenta. `status` es `sent` si llegó a todos, `partial` si "
        "llegó a algunos (revisa `contacts_sent`); si no llegó a ninguno responde 502. "
        "No sustituye a los servicios de emergencia."
    ),
    responses={
        **_RESPONSES,
        status.HTTP_200_OK: {"model": SosRead, "description": "Alerta ya enviada (reintento)."},
    },
)
def send_sos(
    payload: SosRequest,
    response: Response,
    user: CurrentUser,
    db: DbSession,
    sender: EmailSenderDep,
) -> SosRead:
    event, created = service.trigger(db, user, payload, sender)
    if not created:
        response.status_code = status.HTTP_200_OK
    return SosRead(
        id=event.id,
        status=event.status,
        contacts_total=event.contacts_total,
        contacts_sent=event.contacts_sent,
        location_included=service.location_included(event),
        created_at=event.created_at,
    )
