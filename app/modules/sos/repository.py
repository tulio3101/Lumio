import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.sos.models import SosEvent


def get_by_key(db: Session, user_id: uuid.UUID, key: uuid.UUID) -> SosEvent | None:
    return db.scalar(
        select(SosEvent).where(SosEvent.user_id == user_id, SosEvent.idempotency_key == key)
    )


def create(
    db: Session,
    *,
    user_id: uuid.UUID,
    key: uuid.UUID,
    latitude: float | None,
    longitude: float | None,
    accuracy_m: float | None,
    contacts_total: int,
) -> SosEvent:
    event = SosEvent(
        user_id=user_id,
        idempotency_key=key,
        latitude=latitude,
        longitude=longitude,
        accuracy_m=accuracy_m,
        status="pending",
        contacts_total=contacts_total,
        contacts_sent=0,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def finish(db: Session, event: SosEvent, *, contacts_sent: int) -> SosEvent:
    """Cierra el evento: `sent` si llegó a todos, `partial` si a algunos, `failed` si a ninguno."""
    event.contacts_sent = contacts_sent
    if contacts_sent == 0:
        event.status = "failed"
    elif contacts_sent < event.contacts_total:
        event.status = "partial"
    else:
        event.status = "sent"
    db.commit()
    db.refresh(event)
    return event
