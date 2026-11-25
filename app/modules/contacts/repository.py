import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.modules.contacts.models import TrustedContact


def list_for_user(db: Session, user_id: uuid.UUID) -> list[TrustedContact]:
    # Orden estable: el cliente los locuta en ese orden.
    return list(
        db.scalars(
            select(TrustedContact)
            .where(TrustedContact.user_id == user_id)
            .order_by(TrustedContact.created_at, TrustedContact.id)
        )
    )


def count_for_user(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(TrustedContact)
            .where(TrustedContact.user_id == user_id)
        )
        or 0
    )


def get_owned(db: Session, user_id: uuid.UUID, contact_id: uuid.UUID) -> TrustedContact | None:
    """El contacto solo si es de ese usuario."""
    return db.scalar(
        select(TrustedContact).where(
            TrustedContact.id == contact_id, TrustedContact.user_id == user_id
        )
    )


def email_in_use(
    db: Session, user_id: uuid.UUID, email: str, *, excluding: uuid.UUID | None = None
) -> bool:
    query = select(TrustedContact.id).where(
        TrustedContact.user_id == user_id, TrustedContact.email == email
    )
    if excluding is not None:
        query = query.where(TrustedContact.id != excluding)
    return db.scalar(query) is not None


def create(db: Session, user_id: uuid.UUID, name: str, email: str) -> TrustedContact:
    contact = TrustedContact(user_id=user_id, name=name, email=email)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def update(db: Session, contact: TrustedContact, name: str, email: str) -> TrustedContact:
    contact.name = name
    contact.email = email
    db.commit()
    db.refresh(contact)
    return contact


def delete_owned(db: Session, user_id: uuid.UUID, contact_id: uuid.UUID) -> bool:
    """Borra el contacto si es del usuario; dice si existía."""
    result = db.execute(
        delete(TrustedContact).where(
            TrustedContact.id == contact_id, TrustedContact.user_id == user_id
        )
    )
    db.commit()
    return result.rowcount > 0
