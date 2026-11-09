"""Consultar Rutas Recientes contra Postgres real: historial completo, orden y aislamiento."""

import uuid
from datetime import UTC, datetime

from app.modules.places.models import Route
from tests.factories import place, route_payload
from tests.integration.conftest import create_user, login

URL = "/places/routes/active"
HISTORY_URL = "/places/routes/history"


def start_route(api, auth, name: str) -> dict:
    response = api.put(URL, json=route_payload(destination=place(name)), headers=auth)
    assert response.status_code == 200, response.text
    return response.json()


def history(api, auth, **params) -> dict:
    response = api.get(HISTORY_URL, params=params, headers=auth)
    assert response.status_code == 200, response.text
    return response.json()


def test_every_replaced_route_is_kept_newest_first(api, auth):
    pharmacy = start_route(api, auth, "Farmacia Central")
    park = start_route(api, auth, "Parque de los Novios")
    active = start_route(api, auth, "Biblioteca Nacional")

    body = history(api, auth)

    assert [item["id"] for item in body["items"]] == [park["id"], pharmacy["id"]]
    assert active["id"] not in {item["id"] for item in body["items"]}
    assert {item["status"] for item in body["items"]} == {"cancelled"}
    finished = [datetime.fromisoformat(item["finished_at"]) for item in body["items"]]
    assert finished == sorted(finished, reverse=True)
    assert body["total"] == 2


def test_completed_routes_are_ordered_by_when_they_finished(api, user, auth, session_factory):
    start_route(api, auth, "Farmacia Central")
    start_route(api, auth, "Parque de los Novios")  # cancela la farmacia
    data = route_payload(destination=place("Museo del Oro"))
    with session_factory() as session:
        session.add(
            Route(
                id=uuid.uuid4(),
                user_id=user.id,
                origin=data["origin"],
                destination=data["destination"],
                steps=data["steps"],
                distance_meters=data["distance_meters"],
                expected_travel_time_seconds=data["expected_travel_time_seconds"],
                status="completed",
                started_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
                finished_at=datetime(2026, 1, 1, 9, 30, tzinfo=UTC),
            )
        )
        session.commit()

    body = history(api, auth)

    assert [(item["destination"]["name"], item["status"]) for item in body["items"]] == [
        ("Farmacia Central", "cancelled"),
        ("Museo del Oro", "completed"),
    ]


def test_history_only_shows_the_users_routes(api, auth, session_factory):
    start_route(api, auth, "Farmacia Central")
    start_route(api, auth, "Parque de los Novios")
    create_user(session_factory, "beto@example.com")
    other = login(api, "beto@example.com")

    assert history(api, other) == {"items": [], "total": 0, "limit": 20, "offset": 0}
    assert history(api, auth)["total"] == 1


def test_history_is_paginated(api, auth):
    for name in ("Farmacia Central", "Parque de los Novios", "Museo del Oro", "Biblioteca"):
        start_route(api, auth, name)

    body = history(api, auth, limit=2, offset=1)

    assert [item["destination"]["name"] for item in body["items"]] == [
        "Parque de los Novios",
        "Farmacia Central",
    ]
    assert (body["total"], body["limit"], body["offset"]) == (3, 2, 1)


def test_history_requires_the_access_token(api):
    response = api.get(HISTORY_URL)

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_session"
