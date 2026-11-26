"""SCRUM-25: compartir la ubicación con los contactos de confianza."""

import re
from datetime import UTC, datetime, timedelta

import pytest

from app.modules.location_sharing import service
from app.modules.location_sharing.models import LocationShare
from tests.modules.sos.conftest import CREDENTIALS, FakeEmailSender, bearer, mail, token  # noqa: F401

HERE = {"latitude": 4.6097, "longitude": -74.0817, "accuracy_m": 8}
CONTACTS = (("María", "maria@example.com"), ("Pedro", "pedro@example.com"))


@pytest.fixture
def auth(token) -> dict:  # noqa: F811
    return bearer(token)


@pytest.fixture
def contacts(client, auth) -> None:
    for name, email in CONTACTS:
        assert (
            client.post("/contacts", json={"name": name, "email": email}, headers=auth).status_code
            == 201
        )


def link_token(mail_body: str) -> str:
    match = re.search(r"/location-shares/view/([A-Za-z0-9_\-]+)", mail_body)
    assert match, mail_body
    return match.group(1)


def start(client, auth, **extra):
    return client.post("/location-shares", json={**HERE, **extra}, headers=auth)


# MARK: Empezar


def test_starting_emails_a_private_link_to_each_contact(client, auth, contacts, mail):  # noqa: F811
    response = start(client, auth, duration_minutes=30)

    assert response.status_code == 201
    body = response.json()
    assert body["contacts_total"] == 2
    assert body["contacts_sent"] == 2
    assert mail.recipients == ["maria@example.com", "pedro@example.com"]
    assert "comparte su ubicación contigo" in mail.sent[0]["subject"]
    assert "/location-shares/view/" in mail.sent[0]["body"]
    expires = datetime.fromisoformat(body["expires_at"])
    assert timedelta(minutes=29) < expires - datetime.now(UTC) <= timedelta(minutes=30)


def test_the_token_is_not_stored(client, db, auth, contacts, mail):  # noqa: F811
    start(client, auth)
    token_value = link_token(mail.sent[0]["body"])
    share = db.query(LocationShare).one()
    assert token_value not in share.token_hash
    assert share.token_hash == service._hash(token_value)


def test_without_contacts_nothing_is_shared(client, auth, mail):  # noqa: F811
    response = start(client, auth)

    assert response.status_code == 409
    assert response.json()["code"] == "no_trusted_contacts"
    assert mail.sent == []


def test_if_no_contact_gets_the_link_sharing_does_not_start(client, db, auth, contacts, mail):  # noqa: F811
    mail.fail_all = True
    response = start(client, auth)

    assert response.status_code == 502
    assert response.json()["code"] == "location_share_delivery_failed"
    share = db.query(LocationShare).one()
    assert share.stopped_at is not None
    assert share.latitude is None


@pytest.mark.parametrize("minutes", [5, 300])
def test_duration_is_limited(client, auth, contacts, mail, minutes):  # noqa: F811
    assert start(client, auth, duration_minutes=minutes).status_code == 422


def test_requires_a_session(client):
    assert client.post("/location-shares", json=HERE).status_code == 401


def test_starting_again_closes_the_previous_one(client, auth, contacts, mail):  # noqa: F811
    first = start(client, auth).json()["id"]
    old_link = link_token(mail.sent[0]["body"])
    start(client, auth)

    update = client.put(f"/location-shares/{first}/position", json=HERE, headers=auth)
    assert update.status_code == 410
    assert "ya no comparte" in client.get(f"/location-shares/view/{old_link}").text


# MARK: Actualizar y ver


def test_the_page_shows_the_latest_position(client, auth, contacts, mail):  # noqa: F811
    share = start(client, auth).json()["id"]
    moved = {"latitude": 4.7, "longitude": -74.05, "accuracy_m": 12}
    assert (
        client.put(f"/location-shares/{share}/position", json=moved, headers=auth).status_code
        == 204
    )

    page = client.get(f"/location-shares/view/{link_token(mail.sent[0]['body'])}")

    assert page.status_code == 200
    assert "4.700000,-74.050000" in page.text
    assert "12 metros" in page.text
    assert page.headers["cache-control"] == "no-store"
    assert "noindex" in page.headers["x-robots-tag"]
    assert page.headers["referrer-policy"] == "no-referrer"


def test_another_account_cannot_update_or_stop_it(client, auth, contacts, mail):  # noqa: F811
    share = start(client, auth).json()["id"]
    other = {"email": "otro@example.com", "password": "clave-segura-2"}
    client.post("/users", json=other)
    other_auth = bearer(client.post("/users/login", json=other).json()["access_token"])

    assert (
        client.put(f"/location-shares/{share}/position", json=HERE, headers=other_auth).status_code
        == 404
    )
    assert client.delete(f"/location-shares/{share}", headers=other_auth).status_code == 404


def test_unknown_link_is_not_found(client):
    page = client.get("/location-shares/view/no-existe")
    assert page.status_code == 404
    assert "noindex" in page.text


# MARK: Detener y vencer


def test_stopping_ends_the_page_and_forgets_the_position(client, db, auth, contacts, mail):  # noqa: F811
    share = start(client, auth).json()["id"]
    link = link_token(mail.sent[0]["body"])

    assert client.delete(f"/location-shares/{share}", headers=auth).status_code == 204
    assert client.delete(f"/location-shares/{share}", headers=auth).status_code == 204

    page = client.get(f"/location-shares/view/{link}")
    assert "ya no comparte su ubicación" in page.text
    assert "4.609700" not in page.text
    stored = db.query(LocationShare).one()
    assert stored.latitude is None and stored.longitude is None
    assert (
        client.put(f"/location-shares/{share}/position", json=HERE, headers=auth).status_code == 410
    )


def test_an_expired_share_stops_showing_the_position(client, db, auth, contacts, mail):  # noqa: F811
    share_id = start(client, auth).json()["id"]
    link = link_token(mail.sent[0]["body"])
    stored = db.query(LocationShare).one()
    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()

    assert "ya no comparte" in client.get(f"/location-shares/view/{link}").text
    assert (
        client.put(f"/location-shares/{share_id}/position", json=HERE, headers=auth).status_code
        == 410
    )


def test_the_page_escapes_the_display_name():
    html = service.message.page(
        display_name="<script>alert(1)</script>",
        email="a@example.com",
        location=None,
        updated_at=None,
        expires_at=datetime.now(UTC),
        active=True,
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
