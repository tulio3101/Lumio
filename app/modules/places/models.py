import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Una ruta "abierta" es la ruta activa del usuario (en curso o pausada).
OPEN_ROUTE_STATUSES = ("active", "paused")
ROUTE_STATUSES = (*OPEN_ROUTE_STATUSES, "completed", "cancelled")
_OPEN_ROUTE_SQL = text("status IN ('active', 'paused')")


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'cancelled')", name="ck_routes_status"
        ),
        CheckConstraint("current_step >= 0", name="ck_routes_current_step"),
        # Solo una ruta activa por usuario, garantizado también ante peticiones concurrentes.
        Index(
            "uq_routes_one_open_per_user",
            "user_id",
            unique=True,
            postgresql_where=_OPEN_ROUTE_SQL,
            sqlite_where=_OPEN_ROUTE_SQL,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Place serializado: {"name", "latitude", "longitude"}.
    origin: Mapped[dict] = mapped_column(JSON)
    destination: Mapped[dict] = mapped_column(JSON)
    # Lista de RouteStep serializados, ordenados por "order".
    steps: Mapped[list] = mapped_column(JSON, default=list)
    distance_meters: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    expected_travel_time_seconds: Mapped[float] = mapped_column(
        Float, default=0, server_default="0"
    )
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), index=True, default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
