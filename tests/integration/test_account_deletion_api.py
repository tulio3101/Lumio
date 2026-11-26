"""Eliminar Cuenta (SCRUM-7) contra Postgres: el borrado en cascada lo hace la base."""

from sqlalchemy import func, inspect, select

from app.modules.places.models import Route
from app.modules.users.models import AuthSession, User
from tests.factories import finished_route_payload, route_payload

from .conftest import PASSWORD, create_user, login


def count(session_factory, model, user_id=None) -> int:
    query = select(func.count()).select_from(model)
    if user_id is not None:
        query = query.where(model.user_id == user_id)
    with session_factory() as session:
        return session.scalar(query)


def test_deleting_the_account_removes_sessions_routes_and_history(api, session_factory, user, auth):
    other_device = login(api, user.email)
    history = api.post("/places/routes/history", json=finished_route_payload(), headers=auth)
    assert history.status_code == 201
    assert api.put("/places/routes/active", json=route_payload(), headers=auth).status_code == 200

    response = api.delete("/users/me", headers=auth)

    assert response.status_code == 204
    with session_factory() as session:
        assert session.get(User, user.id) is None
    assert count(session_factory, Route, user.id) == 0
    assert count(session_factory, AuthSession, user.id) == 0
    assert api.get("/users/me", headers=other_device).status_code == 401


def test_deleted_account_cannot_sign_in_and_its_email_starts_from_scratch(api, user, auth):
    api.put("/places/routes/active", json=route_payload(), headers=auth)
    api.delete("/users/me", headers=auth)

    credentials = {"email": user.email, "password": PASSWORD}
    assert api.post("/users/login", json=credentials).status_code == 401

    assert api.post("/users", json=credentials).status_code == 201
    fresh = login(api, user.email)
    assert api.get("/places/routes/active", headers=fresh).status_code == 404
    assert api.get("/places/routes/history", headers=fresh).json()["total"] == 0


def test_other_users_are_not_affected(api, session_factory, user, auth):
    luis = create_user(session_factory, "luis@example.com")
    luis_auth = login(api, luis.email)
    api.put("/places/routes/active", json=route_payload(), headers=luis_auth)

    api.delete("/users/me", headers=auth)

    assert api.get("/users/me", headers=luis_auth).status_code == 200
    assert count(session_factory, Route, luis.id) == 1


def test_every_foreign_key_to_users_cascades_in_the_database(engine):
    """Las tablas creadas por las migraciones (no solo los modelos) borran en cascada."""
    inspector = inspect(engine)
    foreign_keys = [
        (table, fk)
        for table in inspector.get_table_names()
        for fk in inspector.get_foreign_keys(table)
        if fk["referred_table"] == "users"
    ]

    assert foreign_keys
    for table, fk in foreign_keys:
        assert fk["options"].get("ondelete") == "CASCADE", table
