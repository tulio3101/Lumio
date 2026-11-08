import uuid

from sqlalchemy import select

from app.modules.places.models import Route
from app.modules.users.dependencies import USER_ID_HEADER
from app.modules.users.models import User
from tests.factories import route_payload

URL = "/places/routes/active"


def headers(user_id: uuid.UUID) -> dict[str, str]:
    return {USER_ID_HEADER: str(user_id)}


def routes_of(session_factory, user_id) -> list[Route]:
    with session_factory() as session:
        return list(
            session.scalars(
                select(Route).where(Route.user_id == user_id).order_by(Route.started_at)
            )
        )


def test_put_persists_route_and_get_returns_it(api, dev_user, session_factory):
    created = api.put(URL, json=route_payload(), headers=headers(dev_user.id))

    assert created.status_code == 200
    [stored] = routes_of(session_factory, dev_user.id)
    assert str(stored.id) == created.json()["id"]
    assert stored.status == "active"
    assert stored.destination["name"] == "Farmacia Central"
    assert [step["order"] for step in stored.steps] == [0, 1, 2]
    assert stored.distance_meters == 320.0
    assert stored.started_at is not None

    fetched = api.get(URL, headers=headers(dev_user.id))

    assert fetched.status_code == 200
    assert fetched.json() == created.json()


def test_new_route_replaces_and_cancels_previous(api, dev_user, session_factory):
    first = api.put(URL, json=route_payload(), headers=headers(dev_user.id)).json()
    second = api.put(
        URL,
        json=route_payload(destination={"name": "Parque", "latitude": 4.62, "longitude": -74.07}),
        headers=headers(dev_user.id),
    ).json()

    stored = {str(r.id): r for r in routes_of(session_factory, dev_user.id)}
    assert stored[first["id"]].status == "cancelled"
    assert stored[first["id"]].finished_at is not None
    assert stored[second["id"]].status == "active"
    assert api.get(URL, headers=headers(dev_user.id)).json()["destination"]["name"] == "Parque"


def test_routes_are_isolated_per_user(api, dev_user, session_factory):
    with session_factory() as session:
        other = User(email="otra@example.com")
        session.add(other)
        session.commit()

    api.put(URL, json=route_payload(), headers=headers(dev_user.id))

    response = api.get(URL, headers=headers(other.id))

    assert response.status_code == 404
    assert response.json()["code"] == "active_route_not_found"


def test_unknown_user_is_rejected_and_nothing_is_persisted(api, session_factory):
    unknown = uuid.uuid4()

    response = api.put(URL, json=route_payload(), headers=headers(unknown))

    assert response.status_code == 401
    assert routes_of(session_factory, unknown) == []


def test_invalid_route_is_not_persisted(api, dev_user, session_factory):
    response = api.put(URL, json=route_payload(steps=[]), headers=headers(dev_user.id))

    assert response.status_code == 422
    assert routes_of(session_factory, dev_user.id) == []
