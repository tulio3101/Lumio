from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.db import DbSession
from app.modules.users import service
from app.modules.users.models import User

_bearer = HTTPBearer(auto_error=False, description="Access token emitido por /users/login")


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
