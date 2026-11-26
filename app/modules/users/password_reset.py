"""Recuperar Contraseña: código de 6 dígitos por correo para cuentas con contraseña propia.

- Pedir un código siempre responde igual, exista o no la cuenta, para no revelar qué correos
  están registrados. Las cuentas solo de Google no tienen contraseña de Lumio: no reciben código.
- El código vence a los 15 minutos, admite 5 intentos y solo vale el último pedido. Se guarda
  solo su hash. Entre dos pedidos de la misma cuenta debe pasar un minuto.
- Al restablecer: nueva contraseña, se cierran todas las sesiones y se borran los códigos.
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.modules.sos.email import EmailDeliveryError, EmailSender
from app.modules.users import repository
from app.modules.users.exceptions import InvalidResetCodeError, PasswordResetError
from app.modules.users.models import User
from app.modules.users.schemas import PasswordResetConfirm, PasswordResetRequest
from app.modules.users.service import normalize_email

logger = logging.getLogger(__name__)

RESET_CODE_MINUTES = 15
RESET_CODE_MAX_ATTEMPTS = 5
RESET_CODE_COOLDOWN = timedelta(minutes=1)

# Se calcula y verifica contra este hash cuando no hay código, para que el tiempo de
# respuesta no revele si la cuenta existe.
_DUMMY_HASH = hash_password("000000")


def _aware(moment: datetime) -> datetime:
    """SQLite (pruebas) devuelve fechas sin zona; Postgres, con zona."""
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def message(code: str) -> tuple[str, str]:
    """Asunto y cuerpo. El código va también dígito a dígito para los lectores de pantalla."""
    subject = "Tu código para recuperar la contraseña de Lumio"
    body = (
        "Pediste recuperar la contraseña de tu cuenta de Lumio.\n\n"
        f"Tu código es: {code}\n"
        f"Dígito a dígito: {' '.join(code)}\n\n"
        f"Escríbelo en la app junto con tu nueva contraseña. Vence en {RESET_CODE_MINUTES} "
        "minutos y solo sirve una vez.\n\n"
        "Si no lo pediste, ignora este correo: tu contraseña no cambia."
    )
    return subject, body


def _own_account(db: Session, email: str) -> User | None:
    user = repository.get_by_email(db, normalize_email(email))
    return user if user is not None and user.password_hash is not None else None


def request_reset(db: Session, payload: PasswordResetRequest, sender: EmailSender) -> None:
    """Envía un código si el correo es de una cuenta propia. No informa si lo es."""
    user = _own_account(db, payload.email)
    if user is None:
        hash_password(new_code())
        return
    now = datetime.now(UTC)
    latest = repository.latest_reset_code(db, user.id)
    if latest is not None and now - _aware(latest.created_at) < RESET_CODE_COOLDOWN:
        return
    code = new_code()
    try:
        repository.replace_reset_code(
            db, user.id, hash_password(code), now, now + timedelta(minutes=RESET_CODE_MINUTES)
        )
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo guardar el código de recuperación de %s", user.id)
        raise PasswordResetError() from exc
    subject, body = message(code)
    try:
        sender.send(to=user.email, subject=subject, body=body)
    except EmailDeliveryError:
        # No se informa al cliente: revelaría que la cuenta existe.
        logger.exception("No se pudo enviar el código de recuperación a %s", user.id)


def confirm_reset(db: Session, payload: PasswordResetConfirm) -> None:
    """Cambia la contraseña si el código es el último, no venció y no agotó los intentos."""
    user = _own_account(db, payload.email)
    code = repository.latest_reset_code(db, user.id) if user is not None else None
    usable = (
        code is not None
        and code.attempts < RESET_CODE_MAX_ATTEMPTS
        and _aware(code.expires_at) > datetime.now(UTC)
    )
    if not usable:
        verify_password(payload.code, _DUMMY_HASH)
        raise InvalidResetCodeError()
    if not verify_password(payload.code, code.code_hash):
        try:
            repository.register_failed_reset_attempt(db, code)
        except SQLAlchemyError:
            db.rollback()
            logger.exception("No se pudo contar el intento fallido de %s", user.id)
        raise InvalidResetCodeError()
    try:
        repository.reset_password(db, user, hash_password(payload.new_password))
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo restablecer la contraseña de %s", user.id)
        raise PasswordResetError() from exc
    logger.info("Contraseña de %s restablecida; todas las sesiones revocadas", user.id)
