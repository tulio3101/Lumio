import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    origin: Mapped[dict] = mapped_column(JSON)
    destination: Mapped[dict] = mapped_column(JSON)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    # active | paused | completed | cancelled; solo una ruta activa por usuario.
    status: Mapped[str] = mapped_column(String(16), index=True, default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
