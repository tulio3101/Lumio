import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.modules.places.exceptions import (
    ActiveRouteConflictError,
    ActiveRouteNotFoundError,
    RouteNotFoundError,
    RouteNotOpenError,
)
from app.modules.places.models import OPEN_ROUTE_STATUSES, Route
from app.modules.places.repository import RouteRepository
from app.modules.places.schemas import RouteCreate, RouteDestinationChange, RouteStatus


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

    def change_destination(
        self, user_id: uuid.UUID, route_id: uuid.UUID, payload: RouteDestinationChange
    ) -> Route:
        """Sustituye el recorrido de una ruta abierta sin crear otra (Modificar Ruta).

        La ruta conserva su id y su inicio; el progreso vuelve al primer paso y, si estaba
        pausada, se reanuda porque el usuario acaba de pedir un recorrido nuevo.
        """
        route = self.routes.get_for_user(route_id, user_id)
        if route is None:
            raise RouteNotFoundError()
        if route.status not in OPEN_ROUTE_STATUSES:
            raise RouteNotOpenError()

        route.origin = payload.origin.model_dump()
        route.destination = payload.destination.model_dump()
        route.steps = [step.model_dump() for step in payload.steps]
        route.distance_meters = payload.distance_meters
        route.expected_travel_time_seconds = payload.expected_travel_time_seconds
        route.current_step = 0
        route.status = RouteStatus.ACTIVE.value
        self.routes.commit()
        return route

    def get_active_route(self, user_id: uuid.UUID) -> Route:
        route = self.routes.get_open_for_user(user_id)
        if route is None:
            raise ActiveRouteNotFoundError()
        return route
