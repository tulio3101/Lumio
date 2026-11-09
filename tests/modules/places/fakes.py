import uuid

from sqlalchemy.exc import IntegrityError

from app.modules.places.models import CLOSED_ROUTE_STATUSES, OPEN_ROUTE_STATUSES, Route


class FakeRouteRepository:
    """Repositorio en memoria con la misma interfaz que RouteRepository."""

    def __init__(self) -> None:
        self.routes: list[Route] = []
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0
        self.fail_commit = False

    def get_open_for_user(self, user_id: uuid.UUID) -> Route | None:
        return next(
            (r for r in self.routes if r.user_id == user_id and r.status in OPEN_ROUTE_STATUSES),
            None,
        )

    def get_for_user(self, route_id: uuid.UUID, user_id: uuid.UUID) -> Route | None:
        return next((r for r in self.routes if r.id == route_id and r.user_id == user_id), None)

    def _closed_for_user(self, user_id: uuid.UUID) -> list[Route]:
        closed = [
            r for r in self.routes if r.user_id == user_id and r.status in CLOSED_ROUTE_STATUSES
        ]
        # Mismo orden que el repositorio real: fin más reciente primero, sin fin al final.
        return sorted(
            closed,
            key=lambda r: (
                r.finished_at is None,
                -r.finished_at.timestamp() if r.finished_at else 0,
                -r.started_at.timestamp(),
            ),
        )

    def list_closed_for_user(self, user_id: uuid.UUID, limit: int, offset: int) -> list[Route]:
        return self._closed_for_user(user_id)[offset : offset + limit]

    def count_closed_for_user(self, user_id: uuid.UUID) -> int:
        return len(self._closed_for_user(user_id))

    def add(self, route: Route) -> Route:
        self.routes.append(route)
        return route

    def flush(self) -> None:
        self.flushes += 1

    def commit(self) -> None:
        if self.fail_commit:
            raise IntegrityError("INSERT INTO routes", {}, Exception("uq_routes_one_open_per_user"))
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1
