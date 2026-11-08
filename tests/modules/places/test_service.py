import uuid
from datetime import UTC, datetime

import pytest

from app.modules.places.exceptions import ActiveRouteConflictError, ActiveRouteNotFoundError
from app.modules.places.schemas import RouteCreate
from app.modules.places.service import RouteService
from tests.factories import route_payload
from tests.modules.places.fakes import FakeRouteRepository

NOW = datetime(2026, 11, 7, 15, 30, tzinfo=UTC)
USER_ID = uuid.uuid4()


@pytest.fixture
def repo() -> FakeRouteRepository:
    return FakeRouteRepository()


@pytest.fixture
def service(repo) -> RouteService:
    return RouteService(repo, now=lambda: NOW)


def payload(**overrides) -> RouteCreate:
    return RouteCreate.model_validate(route_payload(**overrides))


def test_start_active_route_persists_route_as_active(service, repo):
    route = service.start_active_route(USER_ID, payload())

    assert repo.routes == [route]
    assert repo.commits == 1
    assert route.user_id == USER_ID
    assert route.status == "active"
    assert route.current_step == 0
    assert route.started_at == NOW
    assert route.finished_at is None
    assert route.distance_meters == 320.0
    assert route.expected_travel_time_seconds == 260.0
    assert route.destination == {
        "name": "Farmacia Central",
        "latitude": 4.6110,
        "longitude": -74.0790,
    }
    assert [step["instruction"] for step in route.steps] == [
        "Camina hacia el norte por la Carrera 7",
        "Gira a la derecha en la Calle 19",
        "El destino está a tu izquierda",
    ]


def test_new_route_cancels_previous_open_route(service, repo):
    first = service.start_active_route(USER_ID, payload())
    second = service.start_active_route(USER_ID, payload())

    assert first.status == "cancelled"
    assert first.finished_at == NOW
    assert second.status == "active"
    assert repo.get_open_for_user(USER_ID) is second
    # El cierre de la anterior se envía antes de insertar la nueva (índice único).
    assert repo.flushes == 1


def test_paused_route_is_also_replaced(service, repo):
    paused = service.start_active_route(USER_ID, payload())
    paused.status = "paused"

    service.start_active_route(USER_ID, payload())

    assert paused.status == "cancelled"


def test_routes_of_other_users_are_untouched(service, repo):
    other = service.start_active_route(uuid.uuid4(), payload())

    service.start_active_route(USER_ID, payload())

    assert other.status == "active"
    assert repo.flushes == 0


def test_concurrent_write_is_reported_as_conflict(service, repo):
    repo.fail_commit = True

    with pytest.raises(ActiveRouteConflictError):
        service.start_active_route(USER_ID, payload())
    assert repo.rollbacks == 1


def test_get_active_route_returns_open_route(service):
    created = service.start_active_route(USER_ID, payload())

    assert service.get_active_route(USER_ID) is created


def test_get_active_route_without_route_raises_not_found(service):
    with pytest.raises(ActiveRouteNotFoundError):
        service.get_active_route(USER_ID)


def test_finished_routes_are_not_active(service):
    route = service.start_active_route(USER_ID, payload())
    route.status = "completed"

    with pytest.raises(ActiveRouteNotFoundError):
        service.get_active_route(USER_ID)
