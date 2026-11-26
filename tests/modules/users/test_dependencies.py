"""Las rutas identifican al usuario con el access token (Authorization: Bearer)."""

from datetime import timedelta

import pytest

from app.core.security import create_token, decode_token
from app.main import app
from app.modules.places.router import get_route_service
from app.modules.places.service import RouteService
from tests.factories import route_payload
from tests.modules.places.fakes import FakeRouteRepository

from .conftest import bearer

URL = "/places/routes/active"


@pytest.fixture
def repo(client):
    repo = FakeRouteRepository()
    app.dependency_overrides[get_route_service] = lambda: RouteService(repo)
    return repo


def test_route_without_token_returns_401_with_code(client, repo):
    response = client.put(URL, json=route_payload())

    assert response.status_code == 401
    assert response.json() == {"detail": "Sesión no válida", "code": "invalid_session"}
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert repo.routes == []


@pytest.mark.parametrize("token_kind", ["malformado", "refresh", "vencido"])
def test_route_with_invalid_token_returns_401(client, repo, tokens, token_kind):
    claims = decode_token(tokens["access_token"])
    token = {
        "malformado": "no-es-un-jwt",
        "refresh": tokens["refresh_token"],
        "vencido": create_token(claims["sub"], "access", timedelta(seconds=-1), jti=claims["jti"]),
    }[token_kind]

    response = client.put(URL, json=route_payload(), headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_session"
    assert repo.routes == []


def test_route_is_stored_for_the_token_owner(client, repo, tokens):
    response = client.put(URL, json=route_payload(), headers=bearer(tokens["access_token"]))

    assert response.status_code == 200
    owner = decode_token(tokens["access_token"])["sub"]
    assert [str(route.user_id) for route in repo.routes] == [owner]


def test_logged_out_session_cannot_save_routes(client, repo, tokens):
    client.post("/users/logout", json={"refresh_token": tokens["refresh_token"]})

    response = client.put(URL, json=route_payload(), headers=bearer(tokens["access_token"]))

    assert response.status_code == 401
