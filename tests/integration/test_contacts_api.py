"""Contactos de confianza (SCRUM-319) contra Postgres: migración 0006, persistencia y cascada."""

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.modules.contacts.models import TrustedContact
from app.modules.users.models import User

from .conftest import PASSWORD, create_user, login

MARIA = {"name": "María Gómez", "email": "maria@example.com"}


def count_contacts(session_factory) -> int:
    with session_factory() as session:
        return session.scalar(select(func.count()).select_from(TrustedContact))


def test_migration_creates_the_table_with_its_constraints(engine):
    inspector = inspect(engine)

    assert "trusted_contacts" in inspector.get_table_names()
    uniques = {
        tuple(u["column_names"]) for u in inspector.get_unique_constraints("trusted_contacts")
    }
    assert ("user_id", "email") in uniques
    foreign_keys = inspector.get_foreign_keys("trusted_contacts")
    assert foreign_keys[0]["referred_table"] == "users"
    assert foreign_keys[0]["options"].get("ondelete") == "CASCADE"


def test_contacts_are_stored_normalized(api, session_factory, user, auth):
    response = api.post(
        "/contacts", json={"name": " José  Núñez ", "email": " Jose@Example.COM "}, headers=auth
    )

    assert response.status_code == 201
    with session_factory() as session:
        stored = session.scalars(select(TrustedContact)).one()
        assert (stored.user_id, stored.name, stored.email) == (
            user.id,
            "José Núñez",
            "jose@example.com",
        )


def test_contacts_are_still_there_after_signing_in_again(api, user, auth):
    created = api.post("/contacts", json=MARIA, headers=auth).json()
    first = api.post("/users/login", json={"email": user.email, "password": PASSWORD}).json()
    api.post("/users/logout", json={"refresh_token": first["refresh_token"]})

    new_session = login(api, user.email)

    assert api.get("/contacts", headers=new_session).json() == [created]


def test_the_database_rejects_a_repeated_email_for_the_same_user(session_factory, user):
    with session_factory() as session:
        session.add(TrustedContact(user_id=user.id, name="María", email="maria@example.com"))
        session.commit()
        session.add(TrustedContact(user_id=user.id, name="Otra", email="maria@example.com"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_edit_and_delete_are_persisted(api, session_factory, auth):
    contact_id = api.post("/contacts", json=MARIA, headers=auth).json()["id"]

    api.put(
        f"/contacts/{contact_id}", json={"name": "Mari", "email": "mari@example.com"}, headers=auth
    )
    assert api.get("/contacts", headers=auth).json()[0]["email"] == "mari@example.com"

    assert api.delete(f"/contacts/{contact_id}", headers=auth).status_code == 204
    assert count_contacts(session_factory) == 0


def test_each_user_only_reaches_their_own_contacts(api, session_factory, auth):
    contact_id = api.post("/contacts", json=MARIA, headers=auth).json()["id"]
    create_user(session_factory, "luis@example.com")
    luis = login(api, "luis@example.com")

    assert api.get("/contacts", headers=luis).json() == []
    assert api.delete(f"/contacts/{contact_id}", headers=luis).status_code == 404
    assert count_contacts(session_factory) == 1


def test_deleting_the_account_deletes_the_contacts(api, session_factory, user, auth):
    api.post("/contacts", json=MARIA, headers=auth)
    api.post("/contacts", json={"name": "Pedro", "email": "pedro@example.com"}, headers=auth)

    assert api.delete("/users/me", headers=auth).status_code == 204

    assert count_contacts(session_factory) == 0
    with session_factory() as session:
        assert session.get(User, user.id) is None


def test_a_new_account_with_the_same_email_starts_without_contacts(
    api, session_factory, user, auth
):
    api.post("/contacts", json=MARIA, headers=auth)
    api.delete("/users/me", headers=auth)

    create_user(session_factory, "ana@example.com")

    assert api.get("/contacts", headers=login(api, "ana@example.com")).json() == []
