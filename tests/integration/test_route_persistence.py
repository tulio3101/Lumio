import uuid
from datetime import UTC, datetime

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy.exc import IntegrityError

from app.core.db import Base
from app.modules.places.exceptions import ActiveRouteConflictError
from app.modules.places.models import Route
from app.modules.places.repository import RouteRepository
from app.modules.places.schemas import RouteCreate
from app.modules.places.service import RouteService
from app.scripts.seed_dev_user import DEV_USER_EMAIL, seed_dev_user
from tests.factories import route_payload


def make_route(user_id: uuid.UUID, status: str = "active") -> Route:
    return Route(
        id=uuid.uuid4(),
        user_id=user_id,
        origin={"name": "A", "latitude": 0, "longitude": 0},
        destination={"name": "B", "latitude": 1, "longitude": 1},
        steps=[{"order": 0, "instruction": "Sigue", "distance_meters": 1}],
        distance_meters=1,
        expected_travel_time_seconds=1,
        current_step=0,
        status=status,
        started_at=datetime.now(UTC),
    )


def test_migrations_match_models(engine):
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert diff == []


@pytest.mark.parametrize("second_status", ["active", "paused"])
def test_database_allows_only_one_open_route_per_user(session_factory, dev_user, second_status):
    with session_factory() as session:
        session.add(make_route(dev_user.id, "active"))
        session.commit()
        session.add(make_route(dev_user.id, second_status))
        with pytest.raises(IntegrityError, match="uq_routes_one_open_per_user"):
            session.commit()


def test_finished_routes_do_not_block_a_new_active_route(session_factory, dev_user):
    with session_factory() as session:
        session.add_all(
            [
                make_route(dev_user.id, "completed"),
                make_route(dev_user.id, "cancelled"),
                make_route(dev_user.id, "active"),
            ]
        )
        session.commit()


def test_database_rejects_unknown_status(session_factory, dev_user):
    with session_factory() as session:
        session.add(make_route(dev_user.id, "volando"))
        with pytest.raises(IntegrityError, match="ck_routes_status"):
            session.commit()


def test_concurrent_creation_is_reported_as_conflict(session_factory, dev_user):
    """Simula dos peticiones simultáneas: la segunda no vio la ruta creada por la primera."""

    class StaleReadRepository(RouteRepository):
        def get_open_for_user(self, user_id):
            return None

    payload = RouteCreate.model_validate(route_payload())
    with session_factory() as first:
        RouteService(RouteRepository(first)).start_active_route(dev_user.id, payload)

    with session_factory() as second:
        with pytest.raises(ActiveRouteConflictError):
            RouteService(StaleReadRepository(second)).start_active_route(dev_user.id, payload)

    with session_factory() as check:
        assert RouteRepository(check).get_open_for_user(dev_user.id) is not None


def test_deleting_user_deletes_their_routes(session_factory, dev_user):
    with session_factory() as session:
        session.add(make_route(dev_user.id))
        session.commit()
        session.delete(session.merge(dev_user))
        session.commit()
        assert session.query(Route).count() == 0


def test_seed_dev_user_is_idempotent(session_factory):
    with session_factory() as session:
        first = seed_dev_user(session)
        second = seed_dev_user(session)

    assert first.id == second.id
    assert first.email == DEV_USER_EMAIL
