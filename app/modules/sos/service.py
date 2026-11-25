import logging
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.contacts import repository as contacts_repository
from app.modules.sos import message, repository
from app.modules.sos.email import EmailDeliveryError, EmailSender
from app.modules.sos.exceptions import NoTrustedContactsError, SosDeliveryError, SosRecordError
from app.modules.sos.models import SosEvent
from app.modules.sos.schemas import SosRequest
from app.modules.users.models import User

logger = logging.getLogger(__name__)

# Estados con los que el evento ya no se reenvía al repetir la misma llave.
_DELIVERED = ("sent", "partial")


def trigger(
    db: Session, user: User, payload: SosRequest, sender: EmailSender
) -> tuple[SosEvent, bool]:
    """Registra la emergencia y manda un correo por contacto de confianza.

    Devuelve el evento y si esta llamada envió los correos (False: ya estaba entregado).
    Con la misma `idempotency_key`, un evento ya entregado se devuelve tal cual sin enviar de
    nuevo; uno fallido se reintenta. Si el correo no salió a ningún contacto, el evento queda
    `failed` y se lanza SosDeliveryError.
    """
    existing = repository.get_by_key(db, user.id, payload.idempotency_key)
    if existing is not None and existing.status in _DELIVERED:
        return existing, False

    contacts = contacts_repository.list_for_user(db, user.id)
    if not contacts:
        raise NoTrustedContactsError()

    event = existing or _record(db, user, payload, len(contacts))
    sent = _send_all(user, event, [contact.email for contact in contacts], sender)
    try:
        repository.finish(db, event, contacts_sent=sent)
    except OperationalError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo cerrar el evento SOS %s", event.id)
        raise SosRecordError() from exc

    if event.status == "failed":
        raise SosDeliveryError()
    logger.info("SOS %s de %s: %s/%s contactos", event.id, user.id, sent, event.contacts_total)
    return event, True


def _record(db: Session, user: User, payload: SosRequest, contacts_total: int) -> SosEvent:
    try:
        return repository.create(
            db,
            user_id=user.id,
            key=payload.idempotency_key,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy_m=payload.accuracy_m,
            contacts_total=contacts_total,
        )
    except OperationalError:
        db.rollback()
        raise
    except IntegrityError:
        # Dos peticiones con la misma llave a la vez: la otra ya lo registró.
        db.rollback()
        existing = repository.get_by_key(db, user.id, payload.idempotency_key)
        if existing is None:
            raise SosRecordError() from None
        return existing
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("No se pudo registrar el SOS de %s", user.id)
        raise SosRecordError() from exc


def _send_all(user: User, event: SosEvent, recipients: list[str], sender: EmailSender) -> int:
    location = (
        message.Location(event.latitude, event.longitude, event.accuracy_m)
        if location_included(event)
        else None
    )
    subject = message.subject(user.display_name, user.email)
    body = message.body(
        display_name=user.display_name,
        email=user.email,
        sent_at=event.created_at or datetime.now(UTC),
        location=location,
    )
    sent = 0
    for recipient in recipients:
        try:
            sender.send(to=recipient, subject=subject, body=body)
        except EmailDeliveryError:
            # Un contacto que falla no impide avisar a los demás.
            logger.exception("No se pudo enviar el SOS %s a un contacto", event.id)
        else:
            sent += 1
    return sent


def location_included(event: SosEvent) -> bool:
    return event.latitude is not None and event.longitude is not None
