import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.modules.users.models import AuthSession, User


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(db: Session, email: str, password_hash: str) -> User:
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_session(db: Session, user_id: uuid.UUID) -> AuthSession:
    auth_session = AuthSession(user_id=user_id)
    db.add(auth_session)
    db.commit()
    db.refresh(auth_session)
    return auth_session


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_session(db: Session, session_id: uuid.UUID) -> AuthSession | None:
    return db.get(AuthSession, session_id)


def revoke_session(db: Session, auth_session: AuthSession) -> None:
    auth_session.revoked_at = datetime.now(UTC)
    db.commit()


def delete_user(db: Session, user_id: uuid.UUID) -> None:
    """Borra el usuario; la base borra en cascada todo lo que lo referencia (sesiones,
    rutas y las tablas futuras con ``ondelete="CASCADE"``). Si ya no existía, no hace nada.
    """
    db.execute(delete(User).where(User.id == user_id))
    db.commit()


def update_profile(db: Session, user: User, changes: dict[str, str | None]) -> User:
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def change_password(
    db: Session, user: User, password_hash: str, keep_session_id: uuid.UUID
) -> None:
    """Cambia el hash y, en la misma transacción, revoca las demás sesiones activas."""
    user.password_hash = password_hash
    db.execute(
        update(AuthSession)
        .where(
            AuthSession.user_id == user.id,
            AuthSession.id != keep_session_id,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()
