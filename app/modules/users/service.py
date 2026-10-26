from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.users import repository
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate


class EmailAlreadyRegistered(Exception):
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
