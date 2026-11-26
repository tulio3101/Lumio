import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

SOS_STATUSES = ("pending", "sent", "partial", "failed")


class SosEvent(Base):
    """Una activación del botón de emergencia y cuántos contactos recibieron el correo."""

    __tablename__ = "sos_events"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'sent', 'partial', 'failed')", name="ck_sos_status"),
        CheckConstraint(
            "contacts_sent >= 0 AND contacts_sent <= contacts_total", name="ck_sos_counts"
        ),
        # Reintentar con la misma llave no manda correos dobles, también ante peticiones
        # concurrentes.
        UniqueConstraint("user_id", "idempotency_key", name="uq_sos_events_user_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # ON DELETE CASCADE: Eliminar Cuenta (SCRUM-7) borra también sus eventos SOS.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # La genera la app al activar la emergencia.
    idempotency_key: Mapped[uuid.UUID]
    # Nulos si el teléfono no pudo dar la ubicación (sin permiso o sin señal GPS).
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    accuracy_m: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    contacts_total: Mapped[int] = mapped_column(Integer)
    contacts_sent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
