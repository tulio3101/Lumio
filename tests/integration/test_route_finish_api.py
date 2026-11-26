"""Finalizar Ruta contra Postgres real: historial, ruta activa, sincronización tardía."""

import uuid

from tests.factories import finished_route_payload, place, route_payload
from tests.integration.conftest import create_user, login

URL = "/places/routes/active"
HISTORY_URL = "/places/routes/history"


def finish_url(route_id: str) -> str:
    return f"/places/routes/{route_id}/finish"


def start_route(api, auth, name: str) -> dict:
    response = api.put(URL, json=route_payload(destination=place(name)), headers=auth)
    assert response.status_code == 200, response.text
    return response.json()


def finish(api, auth, route_id: str, status: str, finished_at: str = "2030-01-01T00:00:00Z"):
    return api.post(
        finish_url(route_id), json={"status": status, "finished_at": finished_at}, headers=auth
    )


def test_finished_route_is_no_longer_active_and_is_in_the_history(api, auth):
    route = start_route(api, auth, "Farmacia Central")

    response = finish(api, auth, route["id"], "completed")

    assert response.status_code == 200
    assert api.get(URL, headers=auth).status_code == 404
    [item] = api.get(HISTORY_URL, headers=auth).json()["items"]
    assert (item["id"], item["status"]) == (route["id"], "completed")
    assert item["finished_at"]


def test_late_finish_keeps_the_device_time(api, auth):
    route = start_route(api, auth, "Farmacia Central")

    finish(api, auth, route["id"], "cancelled", finished_at=route["started_at"])

    [item] = api.get(HISTORY_URL, headers=auth).json()["items"]
    assert item["status"] == "cancelled"
    assert item["finished_at"] == route["started_at"]


def test_retrying_the_finish_is_safe(api, auth):
    route = start_route(api, auth, "Farmacia Central")
    first = finish(api, auth, route["id"], "completed").json()

    again = finish(api, auth, route["id"], "cancelled")

    assert again.status_code == 200
    assert again.json() == first


def test_other_users_cannot_finish_the_route(api, auth, session_factory):
    route = start_route(api, auth, "Farmacia Central")
    create_user(session_factory, "beto@example.com")
    other = login(api, "beto@example.com")

    assert finish(api, other, route["id"], "completed").status_code == 404
    assert api.get(URL, headers=auth).json()["id"] == route["id"]


def test_offline_route_is_saved_without_touching_the_active_one(api, auth):
    active = start_route(api, auth, "Parque de los Novios")
    payload = finished_route_payload(destination=place("Farmacia Central"))

    created = api.post(HISTORY_URL, json=payload, headers=auth)
    repeated = api.post(HISTORY_URL, json=payload, headers=auth)

    assert created.status_code == 201
    assert repeated.json() == created.json()
    assert api.get(URL, headers=auth).json()["id"] == active["id"]
    body = api.get(HISTORY_URL, headers=auth).json()
    assert [(item["id"], item["status"]) for item in body["items"]] == [
        (payload["id"], "completed")
    ]


def test_offline_route_id_of_another_user_is_a_conflict(api, auth, session_factory):
    payload = finished_route_payload(id=str(uuid.uuid4()))
    assert api.post(HISTORY_URL, json=payload, headers=auth).status_code == 201
    create_user(session_factory, "beto@example.com")
    other = login(api, "beto@example.com")

    response = api.post(HISTORY_URL, json=payload, headers=other)

    assert response.status_code == 409
    assert response.json()["code"] == "route_id_conflict"


def test_finishing_requires_the_access_token(api):
    response = api.post(
        finish_url(uuid.uuid4()),
        json={"status": "completed", "finished_at": "2026-11-08T10:00:00Z"},
    )

    assert response.status_code == 401
