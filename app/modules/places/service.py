import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.modules.places.exceptions import (
    ActiveRouteConflictError,
    ActiveRouteNotFoundError,
    RouteIdConflictError,
    RouteNotFoundError,
    RouteNotOpenError,
)
from app.modules.places.models import OPEN_ROUTE_STATUSES, Route
from app.modules.places.repository import RouteRepository
from app.modules.places.schemas import (
    FinishedRouteCreate,
    RouteCreate,
    RouteDestinationChange,
    RouteFinish,
    RouteStatus,
)


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

    def finish_route(self, user_id: uuid.UUID, route_id: uuid.UUID, payload: RouteFinish) -> Route:
        """Finaliza una ruta abierta (Finalizar Ruta): queda en el historial con su estado.

        La hora de fin es la del dispositivo, acotada entre el inicio de la ruta y ahora.
        Es idempotente: si la ruta ya está cerrada (un reintento tras perder la respuesta,
        o se canceló al iniciar otra) se devuelve sin cambios.
        """
        route = self.routes.get_for_user(route_id, user_id)
        if route is None:
            raise RouteNotFoundError()
        if route.status in OPEN_ROUTE_STATUSES:
            route.status = payload.status.value
            route.finished_at = max(route.started_at, min(payload.finished_at, self.now()))
            self.routes.commit()
        return route

    def record_finished_route(self, user_id: uuid.UUID, payload: FinishedRouteCreate) -> Route:
        """Guarda en el historial una ruta finalizada sin conexión que nunca llegó al backend.

        No toca la ruta abierta del usuario. Reenviar el mismo id devuelve la ruta ya
        guardada; un id que pertenece a otro usuario es un conflicto.
        """
        existing = self.routes.get(payload.id)
        if existing is not None:
            return self._same_user_or_conflict(existing, user_id)

        now = self.now()
        started_at = min(payload.started_at, now)
        route = self.routes.add(
            Route(
                id=payload.id,
                user_id=user_id,
                origin=payload.origin.model_dump(),
                destination=payload.destination.model_dump(),
                steps=[step.model_dump() for step in payload.steps],
                distance_meters=payload.distance_meters,
                expected_travel_time_seconds=payload.expected_travel_time_seconds,
                current_step=0,
                status=payload.status.value,
                started_at=started_at,
                finished_at=max(started_at, min(payload.finished_at, now)),
            )
        )
        try:
            self.routes.commit()
        except IntegrityError as exc:
            # El mismo envío llegó dos veces a la vez: gana el primero.
            self.routes.rollback()
            existing = self.routes.get(payload.id)
            if existing is None:
                raise RouteIdConflictError() from exc
            return self._same_user_or_conflict(existing, user_id)
        return route

    @staticmethod
    def _same_user_or_conflict(route: Route, user_id: uuid.UUID) -> Route:
        if route.user_id != user_id:
            raise RouteIdConflictError()
        return route

    def list_history(self, user_id: uuid.UUID, limit: int, offset: int) -> tuple[list[Route], int]:
        """Historial (Consultar Rutas Recientes): rutas completadas o canceladas del usuario.

        Cada ruta que deja de estar abierta queda guardada, incluida la que se cancela al
        iniciar otra. Se ordenan de la más reciente a la más antigua por la fecha en que
        terminaron. Devuelve la página pedida y el total.
        """
        return (
            self.routes.list_closed_for_user(user_id, limit=limit, offset=offset),
            self.routes.count_closed_for_user(user_id),
        )

    def get_active_route(self, user_id: uuid.UUID) -> Route:
        route = self.routes.get_open_for_user(user_id)
        if route is None:
            raise ActiveRouteNotFoundError()
        return route
