import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.places.exceptions import (
    ActiveRouteConflictError,
    ActiveRouteNotFoundError,
    RouteIdConflictError,
    RouteNotFoundError,
    RouteNotOpenError,
)
from app.modules.places.models import Route
from app.modules.places.schemas import (
    FinishedRouteCreate,
    RouteCreate,
    RouteDestinationChange,
    RouteFinish,
)
from app.modules.places.service import RouteService
from tests.factories import (
    destination_change_payload,
    finished_route_payload,
    place,
    route_payload,
)
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


def change(**overrides) -> RouteDestinationChange:
    return RouteDestinationChange.model_validate(destination_change_payload(**overrides))


def test_change_destination_updates_the_same_route(service, repo):
    route = service.start_active_route(USER_ID, payload())
    route.current_step = 2
    commits_before = repo.commits

    changed = service.change_destination(USER_ID, route.id, change())

    assert changed is route
    assert repo.routes == [route]
    assert repo.commits == commits_before + 1
    assert route.destination["name"] == "Parque de los Novios"
    assert route.origin["latitude"] == 4.6102
    assert [step["instruction"] for step in route.steps] == [
        "Camina hacia el sur por la Calle 19",
        "El destino está a tu derecha",
    ]
    assert route.distance_meters == 80.0
    assert route.expected_travel_time_seconds == 70.0
    assert route.current_step == 0
    assert route.status == "active"
    assert route.started_at == NOW


def test_change_destination_resumes_a_paused_route(service):
    route = service.start_active_route(USER_ID, payload())
    route.status = "paused"

    service.change_destination(USER_ID, route.id, change())

    assert route.status == "active"


@pytest.mark.parametrize("status", ["completed", "cancelled"])
def test_change_destination_of_a_finished_route_is_rejected(service, repo, status):
    route = service.start_active_route(USER_ID, payload())
    route.status = status
    commits_before = repo.commits

    with pytest.raises(RouteNotOpenError):
        service.change_destination(USER_ID, route.id, change())
    assert route.destination["name"] == "Farmacia Central"
    assert repo.commits == commits_before


def test_change_destination_of_another_users_route_is_not_found(service):
    route = service.start_active_route(uuid.uuid4(), payload())

    with pytest.raises(RouteNotFoundError):
        service.change_destination(USER_ID, route.id, change())
    assert route.destination["name"] == "Farmacia Central"


def test_change_destination_of_unknown_route_is_not_found(service):
    with pytest.raises(RouteNotFoundError):
        service.change_destination(USER_ID, uuid.uuid4(), change())


# Historial (Consultar Rutas Recientes)


def closed_route(
    name: str, finished_minute: int | None, status: str = "cancelled", user_id=USER_ID
) -> Route:
    data = route_payload(destination=place(name))
    return Route(
        id=uuid.uuid4(),
        user_id=user_id,
        origin=data["origin"],
        destination=data["destination"],
        steps=data["steps"],
        distance_meters=data["distance_meters"],
        expected_travel_time_seconds=data["expected_travel_time_seconds"],
        current_step=0,
        status=status,
        started_at=NOW,
        finished_at=None if finished_minute is None else NOW + timedelta(minutes=finished_minute),
    )


def names(routes: list[Route]) -> list[str]:
    return [route.destination["name"] for route in routes]


def test_history_lists_closed_routes_newest_first(service, repo):
    repo.routes += [
        closed_route("Farmacia Central", 1),
        closed_route("Biblioteca Nacional", 3, status="completed"),
        closed_route("Parque de los Novios", 2),
    ]

    routes, total = service.list_history(USER_ID, limit=20, offset=0)

    assert names(routes) == ["Biblioteca Nacional", "Parque de los Novios", "Farmacia Central"]
    assert total == 3


def test_history_keeps_the_route_cancelled_by_a_new_one(service):
    first = service.start_active_route(USER_ID, payload(destination=place("Farmacia Central")))
    service.start_active_route(USER_ID, payload(destination=place("Parque de los Novios")))

    routes, total = service.list_history(USER_ID, limit=20, offset=0)

    # La ruta activa no forma parte del historial.
    assert routes == [first]
    assert first.status == "cancelled"
    assert total == 1


def test_history_only_includes_the_users_routes(service, repo):
    repo.routes += [
        closed_route("Farmacia Central", 1),
        closed_route("Otro", 2, user_id=uuid.uuid4()),
    ]

    routes, total = service.list_history(USER_ID, limit=20, offset=0)

    assert names(routes) == ["Farmacia Central"]
    assert total == 1


def test_history_is_paginated_with_the_full_total(service, repo):
    repo.routes += [closed_route(f"Lugar {minute}", minute) for minute in range(1, 6)]

    routes, total = service.list_history(USER_ID, limit=2, offset=1)

    assert names(routes) == ["Lugar 4", "Lugar 3"]
    assert total == 5


def test_empty_history(service):
    assert service.list_history(USER_ID, limit=20, offset=0) == ([], 0)


# Finalizar Ruta


def finish(status: str = "completed", minutes_after_start: int = 20) -> RouteFinish:
    return RouteFinish(status=status, finished_at=NOW + timedelta(minutes=minutes_after_start))


@pytest.fixture
def later(repo) -> RouteService:
    """Servicio media hora después de NOW: las horas de fin del dispositivo ya pasaron."""
    return RouteService(repo, now=lambda: NOW + timedelta(minutes=30))


def test_finish_closes_the_route_with_the_device_time(service, later, repo):
    route = service.start_active_route(USER_ID, payload())

    finished = later.finish_route(USER_ID, route.id, finish("completed", 20))

    assert finished is route
    assert route.status == "completed"
    assert route.finished_at == NOW + timedelta(minutes=20)
    assert later.list_history(USER_ID, limit=20, offset=0) == ([route], 1)
    with pytest.raises(ActiveRouteNotFoundError):
        later.get_active_route(USER_ID)


def test_finish_without_arriving_keeps_it_as_cancelled(service, later):
    route = service.start_active_route(USER_ID, payload())

    later.finish_route(USER_ID, route.id, finish("cancelled"))

    assert route.status == "cancelled"


def test_finish_also_closes_a_paused_route(service, later):
    route = service.start_active_route(USER_ID, payload())
    route.status = "paused"

    later.finish_route(USER_ID, route.id, finish())

    assert route.status == "completed"


def test_finishing_again_changes_nothing(service, later, repo):
    route = service.start_active_route(USER_ID, payload())
    later.finish_route(USER_ID, route.id, finish("completed", 20))
    commits = repo.commits

    again = later.finish_route(USER_ID, route.id, finish("cancelled", 25))

    assert again is route
    assert (route.status, route.finished_at) == ("completed", NOW + timedelta(minutes=20))
    assert repo.commits == commits


def test_finishing_a_route_cancelled_by_a_newer_one_keeps_it(service, later):
    first = service.start_active_route(USER_ID, payload())
    second = service.start_active_route(USER_ID, payload())

    later.finish_route(USER_ID, first.id, finish("completed"))

    assert first.status == "cancelled"
    assert second.status == "active"


@pytest.mark.parametrize("minutes_after_start, expected", [(90, 30), (-10, 0)])
def test_finish_time_is_kept_between_start_and_now(service, later, minutes_after_start, expected):
    route = service.start_active_route(USER_ID, payload())

    later.finish_route(USER_ID, route.id, finish(minutes_after_start=minutes_after_start))

    assert route.finished_at == NOW + timedelta(minutes=expected)


def test_finish_of_another_users_route_is_not_found(service):
    route = service.start_active_route(uuid.uuid4(), payload())

    with pytest.raises(RouteNotFoundError):
        service.finish_route(USER_ID, route.id, finish())
    assert route.status == "active"


def finished(**overrides) -> FinishedRouteCreate:
    return FinishedRouteCreate.model_validate(finished_route_payload(**overrides))


def test_offline_route_is_recorded_in_the_history(service, repo):
    data = finished(started_at="2026-11-07T09:00:00Z", finished_at="2026-11-07T09:20:00Z")

    route = service.record_finished_route(USER_ID, data)

    assert route.id == data.id
    assert route.user_id == USER_ID
    assert route.status == "completed"
    assert route.started_at == datetime(2026, 11, 7, 9, 0, tzinfo=UTC)
    assert route.finished_at == datetime(2026, 11, 7, 9, 20, tzinfo=UTC)
    assert route.destination["name"] == "Farmacia Central"
    assert len(route.steps) == 3
    assert service.list_history(USER_ID, limit=20, offset=0) == ([route], 1)


def test_recording_an_offline_route_does_not_touch_the_active_one(service):
    active = service.start_active_route(USER_ID, payload())

    service.record_finished_route(USER_ID, finished(status="cancelled"))

    assert active.status == "active"
    assert service.get_active_route(USER_ID) is active


def test_recording_the_same_route_twice_does_not_duplicate_it(service, repo):
    data = finished()
    first = service.record_finished_route(USER_ID, data)

    again = service.record_finished_route(USER_ID, data)

    assert again is first
    assert len(repo.routes) == 1


def test_recorded_id_of_another_user_is_a_conflict(service):
    data = finished()
    service.record_finished_route(uuid.uuid4(), data)

    with pytest.raises(RouteIdConflictError):
        service.record_finished_route(USER_ID, data)


def test_recorded_times_in_the_future_are_clamped_to_now(service):
    route = service.record_finished_route(
        USER_ID, finished(started_at="2027-01-01T09:00:00Z", finished_at="2027-01-01T09:20:00Z")
    )

    assert route.started_at == NOW
    assert route.finished_at == NOW
