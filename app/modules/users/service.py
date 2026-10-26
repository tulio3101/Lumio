from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_token, hash_password, verify_password
from app.modules.users import repository
from app.modules.users.models import User
from app.modules.users.schemas import TokenPair, UserCreate, UserLogin

# Se verifica contra este hash cuando el correo no existe, para que el tiempo de
# respuesta no revele qué correos están registrados.
_DUMMY_HASH = hash_password("lumio-dummy-password")


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
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
