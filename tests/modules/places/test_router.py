import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import OperationalError

from app.main import app
from app.modules.places.router import get_route_service
from app.modules.places.service import RouteService
from app.modules.users.dependencies import get_current_user_id
from tests.factories import destination_change_payload, place, route_payload
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


def destination_url(route_id) -> str:
    return f"/places/routes/{route_id}/destination"


def test_change_destination_keeps_route_id_and_replaces_steps(client, repo):
    created = client.put(URL, json=route_payload()).json()

    response = client.put(destination_url(created["id"]), json=destination_change_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["destination"]["name"] == "Parque de los Novios"
    assert [step["order"] for step in body["steps"]] == [0, 1]
    assert body["current_step"] == 0
    assert body["status"] == "active"
    assert client.get(URL).json() == body


def test_change_destination_of_unknown_route_returns_404_with_code(client, repo):
    response = client.put(destination_url(uuid.uuid4()), json=destination_change_payload())

    assert response.status_code == 404
    assert response.json()["code"] == "route_not_found"


def test_change_destination_of_cancelled_route_returns_409(client, repo):
    first = client.put(URL, json=route_payload()).json()
    client.put(URL, json=route_payload())  # cancela la primera

    response = client.put(destination_url(first["id"]), json=destination_change_payload())

    assert response.status_code == 409
    assert response.json()["code"] == "route_not_open"


def test_change_destination_validates_payload(client, repo):
    created = client.put(URL, json=route_payload()).json()

    response = client.put(destination_url(created["id"]), json=destination_change_payload(steps=[]))

    assert response.status_code == 422
    assert client.get(URL).json()["destination"]["name"] == "Farmacia Central"


def test_change_destination_rejects_malformed_route_id(client, repo):
    response = client.put(destination_url("no-es-uuid"), json=destination_change_payload())

    assert response.status_code == 422


def test_destination_change_contract_documents_errors(client):
    spec = client.get("/openapi.json").json()
    change = spec["paths"]["/places/routes/{route_id}/destination"]["put"]

    assert {"200", "401", "404", "409", "422", "503"} <= change["responses"].keys()
    assert {"HTTPBearer": []} in change["security"]


# Historial (Consultar Rutas Recientes)

HISTORY_URL = "/places/routes/history"


@pytest.fixture
def ticking(repo):
    """Servicio con un reloj que avanza un minuto por llamada: fechas de fin distintas."""
    start = datetime(2026, 11, 8, 10, 0, tzinfo=UTC)
    calls = iter(range(1000))
    app.dependency_overrides[get_route_service] = lambda: RouteService(
        repo, now=lambda: start + timedelta(minutes=next(calls))
    )
    return repo


def start_route(client, name: str) -> dict:
    response = client.put(URL, json=route_payload(destination=place(name)))
    assert response.status_code == 200
    return response.json()


def test_history_lists_replaced_routes_newest_first(client, ticking):
    pharmacy = start_route(client, "Farmacia Central")
    park = start_route(client, "Parque de los Novios")
    start_route(client, "Biblioteca Nacional")  # sigue activa

    response = client.get(HISTORY_URL)

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"]] == [park["id"], pharmacy["id"]]
    assert [item["destination"]["name"] for item in body["items"]] == [
        "Parque de los Novios",
        "Farmacia Central",
    ]
    assert {item["status"] for item in body["items"]} == {"cancelled"}
    assert all(item["finished_at"] for item in body["items"])
    assert "steps" not in body["items"][0]
    assert (body["total"], body["limit"], body["offset"]) == (2, 20, 0)


def test_empty_history_returns_an_empty_page(client, repo):
    response = client.get(HISTORY_URL)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_history_pagination_is_applied(client, ticking):
    pharmacy = start_route(client, "Farmacia Central")
    start_route(client, "Parque de los Novios")
    start_route(client, "Biblioteca Nacional")

    body = client.get(HISTORY_URL, params={"limit": 1, "offset": 1}).json()

    assert [item["id"] for item in body["items"]] == [pharmacy["id"]]
    assert (body["total"], body["limit"], body["offset"]) == (2, 1, 1)


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_history_rejects_invalid_pagination(client, repo, params):
    assert client.get(HISTORY_URL, params=params).status_code == 422


def test_history_database_unavailable_returns_503(client, repo):
    def broken_service():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    app.dependency_overrides[get_route_service] = broken_service

    response = client.get(HISTORY_URL)

    assert response.status_code == 503
    assert response.json()["code"] == "database_unavailable"


def test_history_contract_documents_errors(client):
    spec = client.get("/openapi.json").json()
    history = spec["paths"][HISTORY_URL]["get"]

    assert {"200", "401", "422", "503"} <= history["responses"].keys()
    assert {"HTTPBearer": []} in history["security"]
