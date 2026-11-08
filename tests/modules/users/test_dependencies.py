import uuid

import pytest

from app.main import app
from app.modules.places.router import get_route_service
from app.modules.places.service import RouteService
from app.modules.users.dependencies import USER_ID_HEADER, get_user_repository
from app.modules.users.models import User
from tests.factories import route_payload
from tests.modules.places.fakes import FakeRouteRepository

KNOWN_USER = User(id=uuid.uuid4(), email="dev@example.com")


class FakeUserRepository:
    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return KNOWN_USER if user_id == KNOWN_USER.id else None


@pytest.fixture(autouse=True)
def overrides():
    app.dependency_overrides[get_user_repository] = FakeUserRepository
    app.dependency_overrides[get_route_service] = lambda: RouteService(FakeRouteRepository())
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {USER_ID_HEADER: ""},
        {USER_ID_HEADER: "no-es-uuid"},
        {USER_ID_HEADER: str(uuid.uuid4())},
    ],
    ids=["sin-header", "vacio", "malformado", "desconocido"],
)
def test_unidentified_user_gets_401(client, headers):
    response = client.put("/places/routes/active", json=route_payload(), headers=headers)

    assert response.status_code == 401
    assert response.json()["code"] == "user_not_identified"


def test_known_user_is_accepted(client):
    response = client.put(
        "/places/routes/active",
        json=route_payload(),
        headers={USER_ID_HEADER: str(KNOWN_USER.id)},
    )

    assert response.status_code == 200
