import uuid

import pytest
from sqlalchemy.exc import OperationalError

from app.main import app
from app.modules.places.router import get_route_service
from app.modules.places.service import RouteService
from app.modules.users.dependencies import get_current_user_id
from tests.factories import route_payload
from tests.modules.places.fakes import FakeRouteRepository

USER_ID = uuid.uuid4()
URL = "/places/routes/active"


@pytest.fixture
def repo():
    repo = FakeRouteRepository()
    app.dependency_overrides[get_route_service] = lambda: RouteService(repo)
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield repo
    app.dependency_overrides.clear()


def test_put_creates_active_route(client, repo):
    response = client.put(URL, json=route_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["current_step"] == 0
    assert body["destination"]["name"] == "Farmacia Central"
    assert len(body["steps"]) == 3
    assert body["steps"][1]["instruction"] == "Gira a la derecha en la Calle 19"
    assert body["distance_meters"] == 320.0
    assert body["expected_travel_time_seconds"] == 260.0
    assert uuid.UUID(body["id"]) == repo.routes[0].id


def test_get_returns_the_route_created_by_put(client, repo):
    created = client.put(URL, json=route_payload()).json()

    response = client.get(URL)

    assert response.status_code == 200
    assert response.json() == created


def test_get_without_active_route_returns_404_with_code(client, repo):
    response = client.get(URL)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No hay una ruta activa.",
        "code": "active_route_not_found",
    }


def test_conflict_returns_409(client, repo):
    repo.fail_commit = True

    response = client.put(URL, json=route_payload())

    assert response.status_code == 409
    assert response.json()["code"] == "active_route_conflict"


def test_invalid_payload_returns_422(client, repo):
    response = client.put(URL, json=route_payload(steps=[]))

    assert response.status_code == 422
    assert repo.routes == []


def test_database_unavailable_returns_503(client, repo):
    def broken_service():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app.dependency_overrides[get_route_service] = broken_service

    response = client.get(URL)

    assert response.status_code == 503
    assert response.json()["code"] == "database_unavailable"
