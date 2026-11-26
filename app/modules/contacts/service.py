import logging
import uuid

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.contacts import repository
from app.modules.contacts.exceptions import (
    ContactDeleteError,
    ContactDuplicateError,
    ContactIsOwnEmailError,
    ContactLimitReachedError,
    ContactNotFoundError,
    ContactSaveError,
)
from app.modules.contacts.models import MAX_CONTACTS_PER_USER, TrustedContact
from app.modules.contacts.schemas import TrustedContactWrite
from app.modules.users.models import User

logger = logging.getLogger(__name__)


def list_contacts(db: Session, user: User) -> list[TrustedContact]:
    return repository.list_for_user(db, user.id)


def add_contact(db: Session, user: User, payload: TrustedContactWrite) -> TrustedContact:
    """Agrega un contacto. El formato del correo y del nombre ya lo validó el esquema."""
    _check_email_is_allowed(db, user, payload.email)
    if repository.count_for_user(db, user.id) >= MAX_CONTACTS_PER_USER:
        raise ContactLimitReachedError()
    try:
        contact = repository.create(db, user.id, payload.name, payload.email)
    except IntegrityError:
        # Otra petición guardó el mismo correo entre la comprobación y el guardado.
        db.rollback()
        raise ContactDuplicateError() from None
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo guardar un contacto de %s", user.id)
        raise ContactSaveError() from exc
    logger.info("Contacto %s agregado a %s", contact.id, user.id)
    return contact


def edit_contact(
    db: Session, user: User, contact_id: uuid.UUID, payload: TrustedContactWrite
) -> TrustedContact:
    contact = repository.get_owned(db, user.id, contact_id)
    if contact is None:
        raise ContactNotFoundError()
    _check_email_is_allowed(db, user, payload.email, excluding=contact.id)
    try:
        updated = repository.update(db, contact, payload.name, payload.email)
    except IntegrityError:
        db.rollback()
        raise ContactDuplicateError() from None
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo editar el contacto %s de %s", contact_id, user.id)
        raise ContactSaveError() from exc
    return updated


def delete_contact(db: Session, user: User, contact_id: uuid.UUID) -> None:
    try:
        existed = repository.delete_owned(db, user.id, contact_id)
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo eliminar el contacto %s de %s", contact_id, user.id)
        raise ContactDeleteError() from exc
    if not existed:
        raise ContactNotFoundError()


def _check_email_is_allowed(
    db: Session, user: User, email: str, *, excluding: uuid.UUID | None = None
) -> None:
    if email == user.email.strip().lower():
        raise ContactIsOwnEmailError()
    if repository.email_in_use(db, user.id, email, excluding=excluding):
        raise ContactDuplicateError()
