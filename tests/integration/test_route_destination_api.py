"""Modificar Ruta contra Postgres real: misma ruta, nuevo recorrido, aislamiento por usuario."""

import uuid

from sqlalchemy import select

from app.modules.places.models import Route
from app.modules.places.repository import RouteRepository
from app.modules.places.schemas import RouteCreate, RouteDestinationChange
from app.modules.places.service import RouteService
from tests.factories import destination_change_payload, route_payload
from tests.integration.conftest import create_user, login

URL = "/places/routes/active"


def destination_url(route_id: str) -> str:
    return f"/places/routes/{route_id}/destination"


def routes_of(session_factory, user_id) -> list[Route]:
    with session_factory() as session:
        return list(
            session.scalars(
                select(Route).where(Route.user_id == user_id).order_by(Route.started_at)
            )
        )


def test_destination_change_updates_the_same_route(api, user, auth, session_factory):
    created = api.put(URL, json=route_payload(), headers=auth).json()

    changed = api.put(
        destination_url(created["id"]), json=destination_change_payload(), headers=auth
    )

    assert changed.status_code == 200
    assert changed.json()["id"] == created["id"]
    [stored] = routes_of(session_factory, user.id)
    assert str(stored.id) == created["id"]
    assert stored.destination["name"] == "Parque de los Novios"
    assert stored.origin["latitude"] == 4.6102
    assert [step["instruction"] for step in stored.steps] == [
        "Camina hacia el sur por la Calle 19",
        "El destino está a tu derecha",
    ]
    assert stored.current_step == 0
    assert stored.status == "active"
    assert api.get(URL, headers=auth).json() == changed.json()


def test_destination_change_of_another_users_route_is_not_found(api, auth, session_factory):
    created = api.put(URL, json=route_payload(), headers=auth).json()
    create_user(session_factory, "otra@example.com")
    other = login(api, "otra@example.com")

    response = api.put(
        destination_url(created["id"]), json=destination_change_payload(), headers=other
    )

    assert response.status_code == 404
    assert response.json()["code"] == "route_not_found"
    assert api.get(URL, headers=auth).json()["destination"]["name"] == "Farmacia Central"


def test_destination_change_of_replaced_route_is_conflict(api, auth):
    first = api.put(URL, json=route_payload(), headers=auth).json()
    api.put(URL, json=route_payload(), headers=auth)

    response = api.put(
        destination_url(first["id"]), json=destination_change_payload(), headers=auth
    )

    assert response.status_code == 409
    assert response.json()["code"] == "route_not_open"


def test_destination_change_of_unknown_route_is_not_found(api, auth):
    response = api.put(
        destination_url(str(uuid.uuid4())), json=destination_change_payload(), headers=auth
    )

    assert response.status_code == 404


def test_destination_change_is_persisted_in_place(session_factory, user):
    payload = RouteCreate.model_validate(route_payload())
    change = RouteDestinationChange.model_validate(destination_change_payload())
    with session_factory() as session:
        route = RouteService(RouteRepository(session)).start_active_route(user.id, payload)

    with session_factory() as session:
        RouteService(RouteRepository(session)).change_destination(user.id, route.id, change)

    with session_factory() as session:
        [stored] = session.query(Route).all()
        assert stored.id == route.id
        assert stored.destination["name"] == "Parque de los Novios"
        assert [step["order"] for step in stored.steps] == [0, 1]
        assert stored.current_step == 0
        assert stored.status == "active"
