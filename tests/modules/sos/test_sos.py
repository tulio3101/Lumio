import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DataError, OperationalError

from app.modules.sos import repository
from app.modules.sos.models import SosEvent

from .conftest import bearer

LOCATION = {"latitude": 4.6097, "longitude": -74.0817, "accuracy_m": 14.6}


def add_contact(client, token: str, name: str, email: str) -> None:
    response = client.post("/contacts", json={"name": name, "email": email}, headers=bearer(token))
    assert response.status_code == 201


@pytest.fixture
def two_contacts(client, token) -> None:
    add_contact(client, token, "María Gómez", "maria@example.com")
    add_contact(client, token, "Pedro", "pedro@example.com")


def sos(client, token: str, key: uuid.UUID | None = None, **fields):
    body = {"idempotency_key": str(key or uuid.uuid4()), **fields}
    return client.post("/sos", json=body, headers=bearer(token))


def count_events(db) -> int:
    return db.scalar(select(func.count()).select_from(SosEvent))


# --- Envío --------------------------------------------------------------------------


def test_every_contact_gets_one_email_with_the_location(client, token, mail, two_contacts):
    response = sos(client, token, **LOCATION)

    assert response.status_code == 201
    assert response.json()["status"] == "sent"
    assert (response.json()["contacts_total"], response.json()["contacts_sent"]) == (2, 2)
    assert response.json()["location_included"] is True
    assert sorted(mail.recipients) == ["maria@example.com", "pedro@example.com"]
    body = mail.sent[0]["body"]
    assert "https://www.google.com/maps?q=4.609700,-74.081700" in body
    assert "Precisión aproximada: 15 metros." in body


def test_the_email_says_who_sends_it_and_that_it_is_an_emergency(client, token, mail, two_contacts):
    client.patch("/users/me", json={"display_name": "Ana María"}, headers=bearer(token))

    sos(client, token, **LOCATION)

    mail_sent = mail.sent[0]
    assert mail_sent["subject"] == "ALERTA DE EMERGENCIA: Ana María necesita ayuda"
    assert "ALERTA DE EMERGENCIA" in mail_sent["body"]
    assert "Ana María (ana@example.com) activó el botón de emergencia" in mail_sent["body"]
    assert "no sustituye a los servicios de emergencia" in mail_sent["body"]
    assert "123" in mail_sent["body"]


def test_without_a_display_name_the_account_email_identifies_the_sender(
    client, token, mail, two_contacts
):
    sos(client, token, **LOCATION)

    assert mail.sent[0]["subject"] == "ALERTA DE EMERGENCIA: ana@example.com necesita ayuda"
    assert "ana@example.com activó el botón de emergencia" in mail.sent[0]["body"]


def test_without_location_it_is_sent_anyway_saying_so(client, token, mail, two_contacts):
    response = sos(client, token)

    assert response.status_code == 201
    assert response.json()["location_included"] is False
    assert len(mail.sent) == 2
    assert "No se pudo obtener su ubicación" in mail.sent[0]["body"]
    assert "google.com/maps" not in mail.sent[0]["body"]


def test_location_without_accuracy_omits_the_accuracy_line(client, token, mail, two_contacts):
    sos(client, token, latitude=4.6, longitude=-74.0)

    assert "Precisión" not in mail.sent[0]["body"]


def test_the_event_is_recorded(client, db, token, mail, two_contacts):
    key = uuid.uuid4()

    sos(client, token, key, **LOCATION)

    event = db.scalars(select(SosEvent)).one()
    assert event.idempotency_key == key
    assert (event.status, event.contacts_total, event.contacts_sent) == ("sent", 2, 2)
    assert (event.latitude, event.longitude, event.accuracy_m) == (4.6097, -74.0817, 14.6)


# --- Sin contactos, fallos y envío parcial ------------------------------------------


def test_without_contacts_nothing_is_sent_and_it_says_so(client, db, token, mail):
    response = sos(client, token, **LOCATION)

    assert response.status_code == 409
    assert response.json()["code"] == "no_trusted_contacts"
    assert mail.sent == []
    assert count_events(db) == 0


def test_a_failing_contact_does_not_stop_the_others(client, db, token, mail, two_contacts):
    mail.fail_for = {"maria@example.com"}

    response = sos(client, token, **LOCATION)

    assert response.status_code == 201
    assert response.json()["status"] == "partial"
    assert (response.json()["contacts_total"], response.json()["contacts_sent"]) == (2, 1)
    assert mail.recipients == ["pedro@example.com"]
    assert db.scalars(select(SosEvent)).one().status == "partial"


def test_if_no_email_goes_out_it_is_a_502_and_the_event_is_failed(
    client, db, token, mail, two_contacts
):
    mail.fail_all = True

    response = sos(client, token, **LOCATION)

    assert response.status_code == 502
    assert response.json()["code"] == "sos_delivery_failed"
    assert db.scalars(select(SosEvent)).one().status == "failed"


# --- Idempotencia -------------------------------------------------------------------


def test_repeating_a_delivered_alert_does_not_send_again(client, token, mail, two_contacts):
    key = uuid.uuid4()
    first = sos(client, token, key, **LOCATION)

    second = sos(client, token, key, **LOCATION)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    assert len(mail.sent) == 2


def test_a_failed_alert_is_retried_with_the_same_key(client, db, token, mail, two_contacts):
    key = uuid.uuid4()
    mail.fail_all = True
    assert sos(client, token, key, **LOCATION).status_code == 502
    mail.fail_all = False

    retry = sos(client, token, key, **LOCATION)

    assert retry.status_code == 201
    assert retry.json()["status"] == "sent"
    assert len(mail.sent) == 2
    assert count_events(db) == 1


def test_the_same_key_from_another_account_is_a_different_alert(client, token, mail, two_contacts):
    other = {"email": "luis@example.com", "password": "clave-segura-2"}
    client.post("/users", json=other)
    luis = client.post("/users/login", json=other).json()["access_token"]
    add_contact(client, luis, "Marta", "marta@example.com")
    key = uuid.uuid4()
    sos(client, token, key, **LOCATION)

    response = sos(client, luis, key, **LOCATION)

    assert response.status_code == 201
    assert "marta@example.com" in mail.recipients


def test_each_account_only_alerts_its_own_contacts(client, token, mail, two_contacts):
    other = {"email": "luis@example.com", "password": "clave-segura-2"}
    client.post("/users", json=other)
    luis = client.post("/users/login", json=other).json()["access_token"]

    assert sos(client, luis, **LOCATION).status_code == 409
    assert mail.sent == []


# --- Validación y sesión ------------------------------------------------------------


@pytest.mark.parametrize(
    "fields",
    [
        {"latitude": 4.6},
        {"longitude": -74.0},
        {"accuracy_m": 10},
        {"latitude": 91, "longitude": 0},
        {"latitude": 0, "longitude": 181},
        {"latitude": 4.6, "longitude": -74.0, "accuracy_m": -1},
        {"idempotency_key": "no-es-uuid"},
        {"correo": "otro@example.com"},
    ],
)
def test_invalid_requests_are_rejected_and_send_nothing(client, token, mail, two_contacts, fields):
    body = {"idempotency_key": str(uuid.uuid4()), **fields}

    response = client.post("/sos", json=body, headers=bearer(token))

    assert response.status_code == 422
    assert mail.sent == []


def test_the_idempotency_key_is_required(client, token, mail, two_contacts):
    assert client.post("/sos", json=LOCATION, headers=bearer(token)).status_code == 422


def test_it_requires_a_valid_access_token(client, mail, two_contacts):
    body = {"idempotency_key": str(uuid.uuid4())}

    assert client.post("/sos", json=body).status_code == 401
    assert client.post("/sos", json=body, headers=bearer("no-es-token")).status_code == 401
    assert mail.sent == []


# --- Persistencia -------------------------------------------------------------------


def test_deleting_the_account_deletes_its_events(client, db, token, mail, two_contacts):
    sos(client, token, **LOCATION)

    client.delete("/users/me", headers=bearer(token))

    assert count_events(db) == 0


def test_if_the_alert_cannot_be_recorded_nothing_is_sent(
    client, token, mail, two_contacts, monkeypatch
):
    def fail(*_, **__):
        raise DataError("INSERT", {}, Exception("fallo"))

    monkeypatch.setattr(repository, "create", fail)

    response = sos(client, token, **LOCATION)

    assert response.status_code == 500
    assert response.json()["code"] == "sos_record_failed"
    assert mail.sent == []


def test_unavailable_database_is_reported_as_503(client, token, mail, two_contacts, monkeypatch):
    def fail(*_, **__):
        raise OperationalError("SQL", {}, Exception("conexión rechazada"))

    monkeypatch.setattr(repository, "create", fail)

    response = sos(client, token, **LOCATION)

    assert response.status_code == 503
    assert mail.sent == []
