import logging
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.modules.users import repository
from app.modules.users.exceptions import (
    AccountDeletionError,
    GoogleAccountConflictError,
    GoogleEmailNotVerifiedError,
    GoogleSignInError,
    InvalidCurrentPasswordError,
    PasswordChangeError,
    PasswordNotSetError,
    PasswordUnchangedError,
    PreferencesUpdateError,
    ProfileUpdateError,
)
from app.modules.users.google_auth import GoogleIdentity
from app.modules.users.models import AuthSession, User
from app.modules.users.schemas import (
    PasswordChange,
    PreferencesRead,
    PreferencesUpdate,
    TokenPair,
    UserCreate,
    UserLogin,
    UserProfileUpdate,
)

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
    # Siempre se verifica (contra el hash señuelo si no hay uno real) para igualar tiempos,
    # pero el señuelo nunca autentica: su contraseña está en el repo, que es público, y
    # las cuentas solo de Google no tienen password_hash.
    password_ok = verify_password(payload.password, password_hash or _DUMMY_HASH)
    if user is None or password_hash is None or not password_ok:
        raise InvalidCredentials
    return issue_tokens(db, user)


def login_google(db: Session, identity: GoogleIdentity) -> tuple[TokenPair, bool]:
    """Inicia sesión con una identidad de Google ya verificada; crea la cuenta si no existe.

    Devuelve el TokenPair y si la cuenta se acaba de crear. La cuenta se identifica por
    ``sub`` (estable), no por el correo, que en Google puede cambiar. Un correo que ya es de
    una cuenta con contraseña no se vincula solo (GoogleAccountConflictError).
    """
    user = repository.get_by_google_sub(db, identity.sub)
    if user is not None:
        return issue_tokens(db, user), False
    if not identity.email or not identity.email_verified:
        raise GoogleEmailNotVerifiedError()
    email = normalize_email(identity.email)
    if repository.get_by_email(db, email) is not None:
        raise GoogleAccountConflictError()
    try:
        user = repository.create_google_user(db, email, identity.sub)
    except IntegrityError:
        # Otra petición creó la cuenta (mismo sub) o tomó el correo al mismo tiempo.
        db.rollback()
        user = repository.get_by_google_sub(db, identity.sub)
        if user is None:
            raise GoogleAccountConflictError() from None
        return issue_tokens(db, user), False
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo crear la cuenta de Google")
        raise GoogleSignInError() from exc
    logger.info("Cuenta %s creada con Google", user.id)
    return issue_tokens(db, user), True


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


def update_profile(db: Session, user: User, payload: UserProfileUpdate) -> User:
    """Guarda solo los campos enviados (ya validados y normalizados por el esquema)."""
    changes = payload.model_dump(exclude_unset=True)
    try:
        return repository.update_profile(db, user, changes)
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo actualizar el perfil de %s", user.id)
        raise ProfileUpdateError() from exc


def get_preferences(db: Session, user: User) -> PreferencesRead:
    """Las guardadas o, si la cuenta nunca guardó, las predeterminadas (updated_at null)."""
    stored = repository.get_preferences(db, user.id)
    if stored is None:
        return PreferencesRead()
    return PreferencesRead.model_validate(stored)


def update_preferences(db: Session, user: User, payload: PreferencesUpdate) -> PreferencesRead:
    """Reemplaza las preferencias (ya validadas por el esquema). Si otra petición creó la
    fila al mismo tiempo, se reintenta una vez como actualización."""
    values = payload.model_dump(mode="json")
    values["updated_at"] = datetime.now(UTC)
    for attempt in range(2):
        try:
            stored = repository.save_preferences(db, user.id, values)
            return PreferencesRead.model_validate(stored)
        except OperationalError:
            db.rollback()
            raise
        except IntegrityError as exc:
            db.rollback()
            if attempt:
                logger.exception("No se pudieron guardar las preferencias de %s", user.id)
                raise PreferencesUpdateError() from exc
        except SQLAlchemyError as exc:
            db.rollback()
            logger.exception("No se pudieron guardar las preferencias de %s", user.id)
            raise PreferencesUpdateError() from exc
    raise PreferencesUpdateError()


def change_password(db: Session, user: User, session: AuthSession, payload: PasswordChange) -> None:
    """Exige la contraseña actual. Esta sesión sigue abierta; las de los demás
    dispositivos se cierran."""
    if user.password_hash is None:
        raise PasswordNotSetError()
    if not verify_password(payload.current_password, user.password_hash):
        raise InvalidCurrentPasswordError()
    if verify_password(payload.new_password, user.password_hash):
        raise PasswordUnchangedError()
    try:
        repository.change_password(db, user, hash_password(payload.new_password), session.id)
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo cambiar la contraseña de %s", user.id)
        raise PasswordChangeError() from exc
    logger.info("Contraseña de %s cambiada; otras sesiones revocadas", user.id)
