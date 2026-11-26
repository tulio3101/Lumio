import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LocationShare(Base):
    """SCRUM-25: un periodo en que el usuario comparte su ubicación con sus contactos de
    confianza. Solo se guarda la **última** posición (no hay historial) y se borra al detener."""

    __tablename__ = "location_shares"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # ON DELETE CASCADE: Eliminar Cuenta (SCRUM-7) borra también lo compartido.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # SHA-256 del token del enlace que reciben los contactos. El token solo viaja en el correo.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    accuracy_m: Mapped[float | None] = mapped_column(Float)
    position_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    contacts_total: Mapped[int] = mapped_column(Integer)
    contacts_sent: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def is_active(self, now: datetime) -> bool:
        return self.stopped_at is None and _aware(self.expires_at) > now


def _aware(value: datetime) -> datetime:
    # SQLite (pruebas) devuelve fechas sin zona; PostgreSQL, con zona.
    return value if value.tzinfo else value.replace(tzinfo=UTC)
