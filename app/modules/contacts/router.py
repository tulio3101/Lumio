import uuid
from typing import Any

from fastapi import APIRouter, status

from app.core.db import DbSession
from app.core.errors import ErrorResponse
from app.modules.contacts import service
from app.modules.contacts.schemas import TrustedContactRead, TrustedContactWrite
from app.modules.users.dependencies import CurrentUser

router = APIRouter(prefix="/contacts", tags=["contacts"])

_SESSION_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Falta el access token o la sesión no es válida.",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": ErrorResponse,
        "description": "Persistencia no disponible; no se cambió nada.",
    },
}

_RULES = (
    "`name`: 1 a 60 caracteres tras recortar espacios; letras, espacios, apóstrofos, puntos y "
    "guiones. `email`: formato válido; se guarda sin espacios laterales y en minúsculas. No se "
    "repite entre tus contactos, no puede ser el correo de tu cuenta y hay un máximo de 5."
)

_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "El contacto no existe o no es tuyo (`contact_not_found`).",
    },
}


@router.get(
    "",
    response_model=list[TrustedContactRead],
    summary="Listar contactos de confianza",
    description="Los contactos del usuario autenticado, del más antiguo al más reciente.",
    responses=_SESSION_ERRORS,
)
def list_contacts(user: CurrentUser, db: DbSession) -> list[TrustedContactRead]:
    return service.list_contacts(db, user)


@router.post(
    "",
    response_model=TrustedContactRead,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar contacto de confianza",
    description=f"Agrega un contacto que recibirá la alerta por correo. {_RULES}",
    responses={
        **_SESSION_ERRORS,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": (
                "Ya existe un contacto con ese correo (`contact_duplicate`) o ya hay 5 "
                "(`contact_limit_reached`)."
            ),
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "Nombre o correo inválidos, o el correo es el de la cuenta "
                "(`contact_is_own_email`)."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo guardar (`contact_save_failed`); no cambió nada.",
        },
    },
)
def add_contact(
    payload: TrustedContactWrite, user: CurrentUser, db: DbSession
) -> TrustedContactRead:
    return service.add_contact(db, user, payload)


@router.put(
    "/{contact_id}",
    response_model=TrustedContactRead,
    summary="Editar contacto de confianza",
    description=f"Reemplaza el nombre y el correo del contacto. {_RULES}",
    responses={
        **_SESSION_ERRORS,
        **_NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Otro contacto ya tiene ese correo (`contact_duplicate`).",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "Nombre o correo inválidos, o el correo es el de la cuenta "
                "(`contact_is_own_email`)."
            ),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo guardar (`contact_save_failed`); no cambió nada.",
        },
    },
)
def edit_contact(
    contact_id: uuid.UUID, payload: TrustedContactWrite, user: CurrentUser, db: DbSession
) -> TrustedContactRead:
    return service.edit_contact(db, user, contact_id, payload)


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar contacto de confianza",
    description="Elimina el contacto; deja de recibir alertas.",
    responses={
        **_SESSION_ERRORS,
        **_NOT_FOUND,
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "No se pudo eliminar (`contact_delete_failed`); sigue en la lista.",
        },
    },
)
def delete_contact(contact_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    service.delete_contact(db, user, contact_id)
