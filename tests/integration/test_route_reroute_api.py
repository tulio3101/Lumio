"""Recalcular Ruta contra Postgres real: misma ruta y destino, recorrido nuevo, contador."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.modules.places.models import Route
from app.modules.places.repository import RouteRepository
from app.modules.places.schemas import RouteCreate, RouteReroute
from app.modules.places.service import RouteService
from tests.factories import place, reroute_payload, route_payload
from tests.integration.conftest import create_user, login

URL = "/places/routes/active"


def reroute_url(route_id: str) -> str:
    return f"/places/routes/{route_id}/reroute"


def routes_of(session_factory, user_id) -> list[Route]:
    with session_factory() as session:
        return list(
            session.scalars(
                select(Route).where(Route.user_id == user_id).order_by(Route.started_at)
            )
        )


def test_reroute_updates_the_same_route_and_counts_it(api, user, auth, session_factory):
    created = api.put(URL, json=route_payload(), headers=auth).json()
    # El dispositivo recalculó después de iniciar la ruta (la hora se acota a [inicio, ahora]).
    rerouted_at = datetime.now(UTC).isoformat()

    rerouted = api.put(
        reroute_url(created["id"]), json=reroute_payload(rerouted_at=rerouted_at), headers=auth
    )

    assert rerouted.status_code == 200
    assert rerouted.json()["id"] == created["id"]
    [stored] = routes_of(session_factory, user.id)
    assert str(stored.id) == created["id"]
    assert stored.destination["name"] == "Farmacia Central"
    assert stored.origin["latitude"] == 4.6085
    assert [step["instruction"] for step in stored.steps] == [
        "Camina hacia el este por la Calle 17",
        "Gira a la izquierda en la Carrera 5",
        "El destino está a tu derecha",
    ]
    assert stored.distance_meters == 410.0
    assert stored.current_step == 0
    assert stored.status == "active"
    assert stored.reroute_count == 1
    assert stored.last_rerouted_at is not None
    assert stored.started_at <= stored.last_rerouted_at
    assert api.get(URL, headers=auth).json() == rerouted.json()


def test_existing_and_new_routes_start_without_reroutes(api, auth):
    created = api.put(URL, json=route_payload(), headers=auth).json()

    assert created["reroute_count"] == 0
    assert created["last_rerouted_at"] is None


def test_reroute_to_another_destination_is_conflict(api, auth):
    created = api.put(URL, json=route_payload(), headers=auth).json()

    response = api.put(
        reroute_url(created["id"]),
        json=reroute_payload(destination=place("Parque de los Novios", 4.6580, -74.0670)),
        headers=auth,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "route_destination_mismatch"
    active = api.get(URL, headers=auth).json()
    assert active["reroute_count"] == 0
    assert active["steps"] == created["steps"]


def test_reroute_of_another_users_route_is_not_found(api, auth, session_factory):
    created = api.put(URL, json=route_payload(), headers=auth).json()
    create_user(session_factory, "otra@example.com")
    other = login(api, "otra@example.com")

    response = api.put(reroute_url(created["id"]), json=reroute_payload(), headers=other)

    assert response.status_code == 404
    assert response.json()["code"] == "route_not_found"
    assert api.get(URL, headers=auth).json()["reroute_count"] == 0


def test_reroute_of_replaced_route_is_conflict(api, auth):
    first = api.put(URL, json=route_payload(), headers=auth).json()
    api.put(URL, json=route_payload(), headers=auth)

    response = api.put(reroute_url(first["id"]), json=reroute_payload(), headers=auth)

    assert response.status_code == 409
    assert response.json()["code"] == "route_not_open"


def test_reroute_of_unknown_route_is_not_found(api, auth):
    response = api.put(reroute_url(str(uuid.uuid4())), json=reroute_payload(), headers=auth)

    assert response.status_code == 404


def test_reroutes_are_persisted_in_place(session_factory, user):
    payload = RouteCreate.model_validate(route_payload())
    with session_factory() as session:
        route = RouteService(RouteRepository(session)).start_active_route(user.id, payload)

    for _ in range(2):
        change = RouteReroute.model_validate(
            reroute_payload(rerouted_at=datetime.now(UTC).isoformat())
        )
        with session_factory() as session:
            RouteService(RouteRepository(session)).reroute(user.id, route.id, change)

    with session_factory() as session:
        [stored] = session.query(Route).all()
        assert stored.id == route.id
        assert stored.destination["name"] == "Farmacia Central"
        assert [step["order"] for step in stored.steps] == [0, 1, 2]
        assert stored.reroute_count == 2
        assert stored.status == "active"
