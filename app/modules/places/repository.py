import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.places.models import CLOSED_ROUTE_STATUSES, OPEN_ROUTE_STATUSES, Route


class RouteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_open_for_user(self, user_id: uuid.UUID) -> Route | None:
        """Ruta activa o pausada del usuario; el índice único garantiza que hay a lo sumo una."""
        return self.session.scalar(
            select(Route).where(Route.user_id == user_id, Route.status.in_(OPEN_ROUTE_STATUSES))
        )

    def get_for_user(self, route_id: uuid.UUID, user_id: uuid.UUID) -> Route | None:
        """Ruta del usuario por id; None si no existe o pertenece a otro usuario."""
        return self.session.scalar(
            select(Route).where(Route.id == route_id, Route.user_id == user_id)
        )

    def list_closed_for_user(self, user_id: uuid.UUID, limit: int, offset: int) -> list[Route]:
        """Rutas completadas o canceladas, de la que terminó más recientemente a la más antigua."""
        return list(
            self.session.scalars(
                select(Route)
                .where(Route.user_id == user_id, Route.status.in_(CLOSED_ROUTE_STATUSES))
                .order_by(Route.finished_at.desc().nulls_last(), Route.started_at.desc(), Route.id)
                .limit(limit)
                .offset(offset)
            )
        )

    def count_closed_for_user(self, user_id: uuid.UUID) -> int:
        return (
            self.session.scalar(
                select(func.count())
                .select_from(Route)
                .where(Route.user_id == user_id, Route.status.in_(CLOSED_ROUTE_STATUSES))
            )
            or 0
        )

    def add(self, route: Route) -> Route:
        self.session.add(route)
        return route

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
