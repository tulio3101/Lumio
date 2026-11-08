"""Identificación del usuario que hace la petición.

- ``CurrentUser``: usuario autenticado con el access token (``Authorization: Bearer``).
- ``CurrentUserId``: PROVISIONAL para las rutas (SCRUM-8) mientras el cliente iOS no envíe
  el token. El cliente manda el UUID de un usuario existente en ``X-User-Id`` (en
  desarrollo, el que crea ``python -m app.scripts.seed_dev_user``). Para migrar, solo
  cambia ``get_current_user_id`` para devolver el id de ``CurrentUser``; los endpoints que
  dependen de ella no cambian.
"""

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import DbSession, get_db
from app.core.errors import AppError
from app.modules.users import service
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

_bearer = HTTPBearer(auto_error=False, description="Access token emitido por /users/login")

USER_ID_HEADER = "X-User-Id"


class UserNotIdentifiedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "user_not_identified"
    message = "No se pudo identificar al usuario."


def get_user_repository(db: Annotated[Session, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


def get_current_user_id(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    x_user_id: Annotated[
        str | None,
        Header(
            alias=USER_ID_HEADER,
            description="Provisional hasta el login: UUID de un usuario existente.",
        ),
    ] = None,
) -> uuid.UUID:
    if not x_user_id:
        raise UserNotIdentifiedError()
    try:
        user_id = uuid.UUID(x_user_id)
    except ValueError as exc:
        raise UserNotIdentifiedError() from exc
    if users.get_by_id(user_id) is None:
        raise UserNotIdentifiedError()
    return user_id


CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión no válida",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        return service.get_authenticated_user(db, credentials.credentials)
    except service.InvalidToken:
        raise unauthorized from None


CurrentUser = Annotated[User, Depends(get_current_user)]
