"""Crea (o reutiliza) el usuario de desarrollo e imprime su UUID.

Uso: ``python -m app.scripts.seed_dev_user``. Copia el UUID en la clave
``LumioDevUserID`` del Info.plist del cliente iOS. Es idempotente y se niega a
ejecutarse con ``ENVIRONMENT=prod``.
"""

import sys

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

DEV_USER_EMAIL = "dev@example.com"


def seed_dev_user(session: Session) -> User:
    users = UserRepository(session)
    user = users.get_by_email(DEV_USER_EMAIL)
    if user is None:
        user = users.add(User(email=DEV_USER_EMAIL))
        session.commit()
    return user


def main() -> int:
    if get_settings().environment == "prod":
        print("No se siembran usuarios de desarrollo en producción.", file=sys.stderr)
        return 1
    with SessionLocal() as session:
        user = seed_dev_user(session)
    print(user.id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
