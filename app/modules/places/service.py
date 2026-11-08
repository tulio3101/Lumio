import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.modules.places.exceptions import ActiveRouteConflictError, ActiveRouteNotFoundError
from app.modules.places.models import Route
from app.modules.places.repository import RouteRepository
from app.modules.places.schemas import RouteCreate, RouteStatus


class RouteService:
    def __init__(
        self,
        routes: RouteRepository,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.routes = routes
        self.now = now

    def start_active_route(self, user_id: uuid.UUID, payload: RouteCreate) -> Route:
        """Persiste la ruta como activa. Una ruta abierta anterior queda cancelada."""
        timestamp = self.now()
        previous = self.routes.get_open_for_user(user_id)
        if previous is not None:
            previous.status = RouteStatus.CANCELLED.value
            previous.finished_at = timestamp
            # Liberar el índice único antes de insertar la nueva ruta.
            self.routes.flush()

        route = self.routes.add(
            Route(
                id=uuid.uuid4(),
                user_id=user_id,
                origin=payload.origin.model_dump(),
                destination=payload.destination.model_dump(),
                steps=[step.model_dump() for step in payload.steps],
                distance_meters=payload.distance_meters,
                expected_travel_time_seconds=payload.expected_travel_time_seconds,
                current_step=0,
                status=RouteStatus.ACTIVE.value,
                started_at=timestamp,
            )
        )
        try:
            self.routes.commit()
        except IntegrityError as exc:
            # Otra petición del mismo usuario creó una ruta activa al mismo tiempo.
            self.routes.rollback()
            raise ActiveRouteConflictError() from exc
        return route

    def get_active_route(self, user_id: uuid.UUID) -> Route:
        route = self.routes.get_open_for_user(user_id)
        if route is None:
            raise ActiveRouteNotFoundError()
        return route
