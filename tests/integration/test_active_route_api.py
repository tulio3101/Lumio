from sqlalchemy import select

from app.modules.places.models import Route
from tests.factories import route_payload
from tests.integration.conftest import create_user, login

URL = "/places/routes/active"


def routes_of(session_factory, user_id) -> list[Route]:
    with session_factory() as session:
        return list(
            session.scalars(
                select(Route).where(Route.user_id == user_id).order_by(Route.started_at)
            )
        )


def test_put_persists_route_and_get_returns_it(api, user, auth, session_factory):
    created = api.put(URL, json=route_payload(), headers=auth)

    assert created.status_code == 200
    [stored] = routes_of(session_factory, user.id)
    assert str(stored.id) == created.json()["id"]
    assert stored.status == "active"
    assert stored.destination["name"] == "Farmacia Central"
    assert [step["order"] for step in stored.steps] == [0, 1, 2]
    assert stored.distance_meters == 320.0
    assert stored.started_at is not None

    fetched = api.get(URL, headers=auth)

    assert fetched.status_code == 200
    assert fetched.json() == created.json()


def test_new_route_replaces_and_cancels_previous(api, user, auth, session_factory):
    first = api.put(URL, json=route_payload(), headers=auth).json()
    second = api.put(
        URL,
        json=route_payload(destination={"name": "Parque", "latitude": 4.62, "longitude": -74.07}),
        headers=auth,
    ).json()

    stored = {str(r.id): r for r in routes_of(session_factory, user.id)}
    assert stored[first["id"]].status == "cancelled"
    assert stored[first["id"]].finished_at is not None
    assert stored[second["id"]].status == "active"
    assert api.get(URL, headers=auth).json()["destination"]["name"] == "Parque"


def test_routes_are_isolated_per_user(api, auth, session_factory):
    create_user(session_factory, "otra@example.com")
    other = login(api, "otra@example.com")

    api.put(URL, json=route_payload(), headers=auth)

    response = api.get(URL, headers=other)

    assert response.status_code == 404
    assert response.json()["code"] == "active_route_not_found"


def test_request_without_token_is_rejected_and_nothing_is_persisted(api, user, session_factory):
    response = api.put(URL, json=route_payload())

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_session"
    assert routes_of(session_factory, user.id) == []


def test_invalid_route_is_not_persisted(api, user, auth, session_factory):
    response = api.put(URL, json=route_payload(steps=[]), headers=auth)

    assert response.status_code == 422
    assert routes_of(session_factory, user.id) == []
