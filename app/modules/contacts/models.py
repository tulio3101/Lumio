import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Máximo de contactos de confianza por usuario.
MAX_CONTACTS_PER_USER = 5


class TrustedContact(Base):
    """Persona que recibe por correo la alerta del botón de emergencia del usuario."""

    __tablename__ = "trusted_contacts"
    __table_args__ = (
        # El correo (ya en minúsculas) no se repite entre los contactos de un mismo usuario,
        # también ante peticiones concurrentes.
        UniqueConstraint("user_id", "email", name="uq_trusted_contacts_user_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # ON DELETE CASCADE: Eliminar Cuenta (SCRUM-7) borra también sus contactos.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(320))
    # Con microsegundos desde Python: la lista conserva el orden en que se agregaron.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
