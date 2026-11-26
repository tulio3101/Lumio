"""SCRUM-25: compartir la ubicación con los contactos de confianza.

- Empezar requiere al menos un contacto. Se crea un enlace privado (token aleatorio; solo su
  hash queda en la base) y se envía por correo a cada contacto. Uno nuevo cierra el anterior.
- La app envía la posición cada pocos segundos; solo se guarda la última.
- Al detener o al vencer, la página deja de mostrar la ubicación y la posición se borra.
"""

import hashlib
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.contacts import repository as contacts_repository
from app.modules.location_sharing import message
from app.modules.location_sharing.exceptions import (
    LocationShareDeliveryError,
    LocationShareEndedError,
    LocationShareNotFoundError,
    NoTrustedContactsError,
)
from app.modules.location_sharing.models import LocationShare
from app.modules.location_sharing.schemas import LocationShareStart, Position
from app.modules.sos.email import EmailDeliveryError, EmailSender
from app.modules.sos.message import Location
from app.modules.users.models import User

logger = logging.getLogger(__name__)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def view_link(token: str) -> str:
    base = get_settings().public_base_url.rstrip("/")
    return f"{base}/location-shares/view/{token}"


def start(
    db: Session, user: User, payload: LocationShareStart, sender: EmailSender, now: datetime
) -> LocationShare:
    contacts = contacts_repository.list_for_user(db, user.id)
    if not contacts:
        raise NoTrustedContactsError()

    for active in _active_for_user(db, user.id, now):
        _close(active, now)

    token = secrets.token_urlsafe(32)
    share = LocationShare(
        user_id=user.id,
        token_hash=_hash(token),
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy_m=payload.accuracy_m,
        position_updated_at=now,
        contacts_total=len(contacts),
        started_at=now,
        expires_at=now + timedelta(minutes=payload.duration_minutes),
    )
    db.add(share)
    db.flush()

    subject = message.subject(user.display_name, user.email)
    body = message.body(
        display_name=user.display_name,
        email=user.email,
        link=view_link(token),
        expires_at=share.expires_at,
    )
    sent = 0
    for contact in contacts:
        try:
            sender.send(to=contact.email, subject=subject, body=body)
        except EmailDeliveryError:
            # Un contacto que falla no impide avisar a los demás.
            logger.exception("No se pudo enviar el enlace de ubicación %s a un contacto", share.id)
        else:
            sent += 1
    share.contacts_sent = sent
    if sent == 0:
        # Nadie recibió el enlace: no tiene sentido seguir recibiendo posiciones.
        _close(share, now)
        db.commit()
        raise LocationShareDeliveryError()
    db.commit()
    logger.info(
        "Ubicación compartida %s de %s con %s/%s contactos", share.id, user.id, sent, len(contacts)
    )
    return share


def update_position(
    db: Session, user: User, share_id: uuid.UUID, position: Position, now: datetime
) -> None:
    share = _owned(db, user, share_id)
    if not share.is_active(now):
        raise LocationShareEndedError()
    share.latitude = position.latitude
    share.longitude = position.longitude
    share.accuracy_m = position.accuracy_m
    share.position_updated_at = now
    db.commit()


def stop(db: Session, user: User, share_id: uuid.UUID, now: datetime) -> None:
    share = _owned(db, user, share_id)
    if share.stopped_at is None:
        _close(share, now)
        db.commit()


def page_for_token(db: Session, token: str, now: datetime) -> str | None:
    share = db.scalar(select(LocationShare).where(LocationShare.token_hash == _hash(token)))
    if share is None:
        return None
    user = db.get(User, share.user_id)
    if user is None:
        return None
    active = share.is_active(now)
    location = (
        Location(share.latitude, share.longitude, share.accuracy_m)
        if active and share.latitude is not None and share.longitude is not None
        else None
    )
    return message.page(
        display_name=user.display_name,
        email=user.email,
        location=location,
        updated_at=share.position_updated_at if active else None,
        expires_at=share.expires_at,
        active=active,
    )


def _owned(db: Session, user: User, share_id: uuid.UUID) -> LocationShare:
    share = db.get(LocationShare, share_id)
    if share is None or share.user_id != user.id:
        raise LocationShareNotFoundError()
    return share


def _active_for_user(db: Session, user_id: uuid.UUID, now: datetime) -> list[LocationShare]:
    shares = db.scalars(
        select(LocationShare).where(
            LocationShare.user_id == user_id, LocationShare.stopped_at.is_(None)
        )
    ).all()
    return [share for share in shares if share.is_active(now)]


def _close(share: LocationShare, now: datetime) -> None:
    """Termina y borra la posición: después de detener no queda dónde estuvo."""
    share.stopped_at = now
    share.latitude = None
    share.longitude = None
    share.accuracy_m = None
    share.position_updated_at = None


def utcnow() -> datetime:
    return datetime.now(UTC)
