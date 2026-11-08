"""Identificación del usuario que hace la petición.

PROVISIONAL: mientras no exista el inicio de sesión, el cliente envía el UUID de un
usuario existente en el header ``X-User-Id`` (en desarrollo, el que crea
``python -m app.scripts.seed_dev_user``). Cuando exista el login, solo cambia
``get_current_user_id`` para leer el ``sub`` del access token; los endpoints que
dependen de ella no cambian.
"""

import uuid
from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.modules.users.repository import UserRepository

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
