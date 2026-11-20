import logging
import uuid
from datetime import timedelta

import jwt
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.modules.users import repository
from app.modules.users.exceptions import AccountDeletionError
from app.modules.users.models import AuthSession, User
from app.modules.users.schemas import TokenPair, UserCreate, UserLogin

logger = logging.getLogger(__name__)

# Se verifica contra este hash cuando el correo no existe, para que el tiempo de
# respuesta no revele qué correos están registrados.
_DUMMY_HASH = hash_password("lumio-dummy-password")


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class InvalidToken(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register(db: Session, payload: UserCreate) -> User:
    email = normalize_email(payload.email)
    if repository.get_by_email(db, email):
        raise EmailAlreadyRegistered
    try:
        return repository.create_user(db, email, hash_password(payload.password))
    except IntegrityError:
        db.rollback()
        raise EmailAlreadyRegistered from None


def issue_tokens(db: Session, user: User) -> TokenPair:
    settings = get_settings()
    session_id = str(repository.create_session(db, user.id).id)
    access_ttl = timedelta(minutes=settings.access_token_minutes)
    return TokenPair(
        access_token=create_token(str(user.id), "access", access_ttl, jti=session_id),
        refresh_token=create_token(
            str(user.id), "refresh", timedelta(days=settings.refresh_token_days), jti=session_id
        ),
        expires_in=int(access_ttl.total_seconds()),
    )


def login(db: Session, payload: UserLogin) -> TokenPair:
    user = repository.get_by_email(db, normalize_email(payload.email))
    password_hash = user.password_hash if user else None
    if not verify_password(payload.password, password_hash or _DUMMY_HASH) or user is None:
        raise InvalidCredentials
    return issue_tokens(db, user)


def resolve_session(db: Session, token: str, token_type: str) -> AuthSession:
    """Devuelve la sesión activa a la que pertenece el token o lanza InvalidToken."""
    try:
        claims = decode_token(token)
        session = repository.get_session(db, uuid.UUID(claims["jti"]))
        valid = claims["type"] == token_type and str(session.user_id) == claims["sub"]
    except (jwt.InvalidTokenError, KeyError, ValueError, AttributeError):
        raise InvalidToken from None
    if not valid or session.revoked_at is not None:
        raise InvalidToken
    return session


def get_authenticated_user(db: Session, access_token: str) -> User:
    session = resolve_session(db, access_token, "access")
    user = repository.get_by_id(db, session.user_id)
    if user is None:
        raise InvalidToken
    return user


def refresh(db: Session, refresh_token: str) -> TokenPair:
    """Rota la sesión: el refresh token usado deja de ser válido."""
    session = resolve_session(db, refresh_token, "refresh")
    user = repository.get_by_id(db, session.user_id)
    if user is None:
        raise InvalidToken
    repository.revoke_session(db, session)
    return issue_tokens(db, user)


def logout(db: Session, refresh_token: str) -> None:
    repository.revoke_session(db, resolve_session(db, refresh_token, "refresh"))


def delete_account(db: Session, user: User) -> None:
    """Elimina la cuenta y, en cascada, sus sesiones, rutas y demás datos asociados.

    Después ningún token de la cuenta es válido y el correo queda libre para registrar
    una cuenta nueva, que no hereda nada de la anterior.
    """
    try:
        repository.delete_user(db, user.id)
    except OperationalError:
        # Base de datos caída: el manejador global responde 503 y la cuenta sigue intacta.
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo eliminar la cuenta %s", user.id)
        raise AccountDeletionError() from exc
    logger.info("Cuenta %s eliminada", user.id)
