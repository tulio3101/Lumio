"""Botón de emergencia (SCRUM-35) contra Postgres: migración 0007, idempotencia y cascada."""

import uuid

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.modules.sos.email import get_email_sender
from app.modules.sos.models import SosEvent
from tests.modules.sos.conftest import FakeEmailSender

from .conftest import create_user, login

CONTACTS = (("María", "maria@example.com"), ("Pedro", "pedro@example.com"))


@pytest.fixture
def mail(api) -> FakeEmailSender:
    sender = FakeEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: sender
    return sender


def add_contacts(api, auth) -> None:
    for name, email in CONTACTS:
        response = api.post("/contacts", json={"name": name, "email": email}, headers=auth)
        assert response.status_code == 201


def count_events(session_factory) -> int:
    with session_factory() as session:
        return session.scalar(select(func.count()).select_from(SosEvent))


def event(user, key, *, sent=1, total=1) -> SosEvent:
    return SosEvent(
        user_id=user.id,
        idempotency_key=key,
        status="sent",
        contacts_total=total,
        contacts_sent=sent,
    )


def test_migration_creates_the_table_with_its_constraints(engine):
    inspector = inspect(engine)

    assert "sos_events" in inspector.get_table_names()
    uniques = {tuple(u["column_names"]) for u in inspector.get_unique_constraints("sos_events")}
    assert ("user_id", "idempotency_key") in uniques
    assert inspector.get_foreign_keys("sos_events")[0]["options"].get("ondelete") == "CASCADE"


def test_the_alert_is_sent_and_recorded(api, session_factory, user, auth, mail):
    add_contacts(api, auth)
    key = uuid.uuid4()
    body = {"idempotency_key": str(key), "latitude": 4.6097, "longitude": -74.0817, "accuracy_m": 9}

    response = api.post("/sos", json=body, headers=auth)

    assert response.status_code == 201
    assert sorted(mail.recipients) == ["maria@example.com", "pedro@example.com"]
    with session_factory() as session:
        stored = session.scalars(select(SosEvent)).one()
        assert (stored.user_id, stored.idempotency_key, stored.status) == (user.id, key, "sent")
        assert (stored.contacts_total, stored.contacts_sent) == (2, 2)


def test_repeating_the_alert_does_not_send_twice(api, auth, mail):
    add_contacts(api, auth)
    body = {"idempotency_key": str(uuid.uuid4())}
    api.post("/sos", json=body, headers=auth)

    again = api.post("/sos", json=body, headers=auth)

    assert again.status_code == 200
    assert len(mail.sent) == 2


def test_the_database_rejects_a_repeated_key_for_the_same_user(session_factory, user):
    key = uuid.uuid4()
    with session_factory() as session:
        session.add(event(user, key))
        session.commit()
        session.add(event(user, key))
        with pytest.raises(IntegrityError):
            session.commit()


def test_the_database_rejects_impossible_counts(session_factory, user):
    with session_factory() as session:
        session.add(event(user, uuid.uuid4(), sent=2, total=1))
        with pytest.raises(IntegrityError):
            session.commit()


def test_a_failed_alert_is_retried_with_the_same_key(api, session_factory, auth, mail):
    add_contacts(api, auth)
    body = {"idempotency_key": str(uuid.uuid4())}
    mail.fail_all = True
    assert api.post("/sos", json=body, headers=auth).status_code == 502
    mail.fail_all = False

    assert api.post("/sos", json=body, headers=auth).status_code == 201
    assert count_events(session_factory) == 1


def test_each_user_only_alerts_their_own_contacts(api, session_factory, auth, mail):
    add_contacts(api, auth)
    create_user(session_factory, "luis@example.com")
    luis = login(api, "luis@example.com")

    response = api.post("/sos", json={"idempotency_key": str(uuid.uuid4())}, headers=luis)

    assert response.status_code == 409
    assert mail.sent == []


def test_deleting_the_account_deletes_the_events(api, session_factory, auth, mail):
    add_contacts(api, auth)
    api.post("/sos", json={"idempotency_key": str(uuid.uuid4())}, headers=auth)

    assert api.delete("/users/me", headers=auth).status_code == 204

    assert count_events(session_factory) == 0
