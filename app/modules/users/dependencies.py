"""Identificación del usuario que hace la petición con el access token.

- ``CurrentUser``: usuario autenticado (``Authorization: Bearer <access_token>``).
- ``CurrentSession``: la sesión (dispositivo) del access token, p. ej. para cerrar las
  demás al cambiar la contraseña.
- ``CurrentUserId``: solo su id, para módulos que no necesitan el usuario completo
  (por ejemplo, las rutas). Así no dependen de cómo se autentica la petición.
"""

import uuid
from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.db import DbSession
from app.core.errors import AppError
from app.modules.users import service
from app.modules.users.models import AuthSession, User

_bearer = HTTPBearer(auto_error=False, description="Access token emitido por /users/login")


class InvalidSessionError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "invalid_session"
    message = "Sesión no válida"
    headers = {"WWW-Authenticate": "Bearer"}


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise InvalidSessionError()
    try:
        return service.get_authenticated_user(db, credentials.credentials)
    except service.InvalidToken:
        raise InvalidSessionError() from None


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_user_id(user: CurrentUser) -> uuid.UUID:
    return user.id


CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


def get_current_session(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthSession:
    if credentials is None:
        raise InvalidSessionError()
    try:
        return service.resolve_session(db, credentials.credentials, "access")
    except service.InvalidToken:
        raise InvalidSessionError() from None


CurrentSession = Annotated[AuthSession, Depends(get_current_session)]
