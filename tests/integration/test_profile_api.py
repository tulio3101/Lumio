"""Personalizar Cuenta (SCRUM-6) contra Postgres: migración 0005, perfil y contraseña."""

from sqlalchemy import select

from app.modules.users.models import AuthSession, User

from .conftest import PASSWORD, login

NEW_PASSWORD = "otra-clave-segura"


def test_profile_is_persisted_and_read_back(api, session_factory, user, auth):
    response = api.patch(
        "/users/me", json={"display_name": " José  Núñez ", "phone": "310 555-0101"}, headers=auth
    )

    assert response.status_code == 200
    with session_factory() as session:
        stored = session.get(User, user.id)
        assert (stored.display_name, stored.phone) == ("José Núñez", "3105550101")
    assert api.get("/users/me", headers=auth).json()["display_name"] == "José Núñez"


def test_invalid_profile_does_not_touch_the_database(api, session_factory, user, auth):
    api.patch("/users/me", json={"display_name": "Ana"}, headers=auth)

    response = api.patch("/users/me", json={"display_name": "Ana", "phone": "123"}, headers=auth)

    assert response.status_code == 422
    with session_factory() as session:
        assert session.get(User, user.id).phone is None


def test_profile_can_be_cleared(api, session_factory, user, auth):
    api.patch("/users/me", json={"display_name": "Ana", "phone": "3001234567"}, headers=auth)

    api.patch("/users/me", json={"display_name": None, "phone": ""}, headers=auth)

    with session_factory() as session:
        stored = session.get(User, user.id)
        assert (stored.display_name, stored.phone) == (None, None)


def test_changing_the_password_revokes_only_the_other_sessions(api, session_factory, user, auth):
    other_device = login(api, user.email)

    response = api.put(
        "/users/me/password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=auth,
    )

    assert response.status_code == 204
    with session_factory() as session:
        sessions = session.scalars(select(AuthSession).where(AuthSession.user_id == user.id)).all()
        assert sorted(s.revoked_at is None for s in sessions) == [False, True]
    assert api.get("/users/me", headers=auth).status_code == 200
    assert api.get("/users/me", headers=other_device).status_code == 401
    old = api.post("/users/login", json={"email": user.email, "password": PASSWORD})
    new = api.post("/users/login", json={"email": user.email, "password": NEW_PASSWORD})
    assert (old.status_code, new.status_code) == (401, 200)


def test_wrong_current_password_changes_nothing(api, user, auth):
    other_device = login(api, user.email)

    response = api.put(
        "/users/me/password",
        json={"current_password": "no-es-la-clave", "new_password": NEW_PASSWORD},
        headers=auth,
    )

    assert response.status_code == 403
    assert api.get("/users/me", headers=other_device).status_code == 200
    assert (
        api.post("/users/login", json={"email": user.email, "password": PASSWORD}).status_code
        == 200
    )
