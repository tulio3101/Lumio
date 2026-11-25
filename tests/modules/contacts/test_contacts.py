import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DataError, IntegrityError, OperationalError

from app.modules.contacts import repository
from app.modules.contacts.models import MAX_CONTACTS_PER_USER, TrustedContact

from .conftest import MARIA, bearer


def add(client, token: str, body: dict):
    return client.post("/contacts", json=body, headers=bearer(token))


def edit(client, token: str, contact_id, body: dict):
    return client.put(f"/contacts/{contact_id}", json=body, headers=bearer(token))


def remove(client, token: str, contact_id):
    return client.delete(f"/contacts/{contact_id}", headers=bearer(token))


def listing(client, token: str) -> list[dict]:
    response = client.get("/contacts", headers=bearer(token))
    assert response.status_code == 200
    return response.json()


def contact(name: str = "María Gómez", email: str = "maria@example.com") -> dict:
    return {"name": name, "email": email}


# --- Alta y listado -----------------------------------------------------------------


def test_new_account_has_no_contacts(client, token):
    assert listing(client, token) == []


def test_a_contact_is_added_and_listed(client, token):
    response = add(client, token, MARIA)

    assert response.status_code == 201
    created = response.json()
    assert (created["name"], created["email"]) == ("María Gómez", "maria@example.com")
    assert uuid.UUID(created["id"])
    assert listing(client, token) == [created]


def test_contacts_are_listed_in_the_order_they_were_added(client, token):
    for index in range(3):
        add(client, token, contact(name=f"Contacto {chr(65 + index)}", email=f"c{index}@mail.com"))

    assert [item["name"] for item in listing(client, token)] == [
        "Contacto A",
        "Contacto B",
        "Contacto C",
    ]


def test_name_and_email_are_normalized_before_saving(client, token):
    response = add(
        client, token, contact(name="  José   Núñez ", email="  Maria.Gomez@Example.COM ")
    )

    assert response.status_code == 201
    assert response.json()["name"] == "José Núñez"
    assert response.json()["email"] == "maria.gomez@example.com"


# --- Validación (SCRUM-346) ---------------------------------------------------------


@pytest.mark.parametrize(
    "email",
    ["", "maria", "maria@", "@example.com", "maria@example", "mar ia@example.com", "a@b@c.com"],
)
def test_an_invalid_email_is_rejected_and_nothing_is_saved(client, token, email):
    response = add(client, token, contact(email=email))

    assert response.status_code == 422
    assert listing(client, token) == []


@pytest.mark.parametrize("name", ["", "   ", "R2-D2", "María <b>", "...", "A" * 61])
def test_an_invalid_name_is_rejected(client, token, name):
    assert add(client, token, contact(name=name)).status_code == 422
    assert listing(client, token) == []


@pytest.mark.parametrize(
    "body",
    [
        {"email": "maria@example.com"},
        {"name": "María"},
        {},
        {"name": None, "email": "maria@example.com"},
        {"name": "María", "email": None},
        {**MARIA, "user_id": str(uuid.uuid4())},
    ],
)
def test_name_and_email_are_both_required_and_nothing_else_is_accepted(client, token, body):
    assert add(client, token, body).status_code == 422


def test_sixty_characters_and_accents_are_allowed_in_the_name(client, token):
    name = "Ñ" + "á" * 59

    assert add(client, token, contact(name=name)).json()["name"] == name


def test_the_same_email_cannot_be_added_twice_even_with_other_case(client, token):
    add(client, token, MARIA)

    response = add(client, token, contact(name="Otra María", email="MARIA@example.com "))

    assert response.status_code == 409
    assert response.json()["code"] == "contact_duplicate"
    assert len(listing(client, token)) == 1


def test_your_own_email_cannot_be_a_contact(client, token):
    response = add(client, token, contact(email="Ana@Example.com"))

    assert response.status_code == 422
    assert response.json()["code"] == "contact_is_own_email"
    assert listing(client, token) == []


def test_there_is_a_maximum_of_contacts(client, token):
    for index in range(MAX_CONTACTS_PER_USER):
        assert add(client, token, contact(email=f"c{index}@mail.com")).status_code == 201

    response = add(client, token, contact(email="uno-mas@mail.com"))

    assert response.status_code == 409
    assert response.json()["code"] == "contact_limit_reached"
    assert len(listing(client, token)) == MAX_CONTACTS_PER_USER


def test_deleting_one_frees_a_place_at_the_limit(client, token):
    ids = [
        add(client, token, contact(email=f"c{index}@mail.com")).json()["id"]
        for index in range(MAX_CONTACTS_PER_USER)
    ]
    remove(client, token, ids[0])

    assert add(client, token, contact(email="nuevo@mail.com")).status_code == 201


# --- Edición ------------------------------------------------------------------------


def test_a_contact_is_edited(client, token):
    contact_id = add(client, token, MARIA).json()["id"]

    response = edit(client, token, contact_id, contact(name="María José", email="mj@mail.com"))

    assert response.status_code == 200
    assert response.json()["id"] == contact_id
    assert (response.json()["name"], response.json()["email"]) == ("María José", "mj@mail.com")
    assert listing(client, token) == [response.json()]


def test_a_contact_keeps_its_email_when_only_the_name_changes(client, token):
    contact_id = add(client, token, MARIA).json()["id"]

    response = edit(client, token, contact_id, contact(name="Mari"))

    assert response.status_code == 200
    assert response.json()["name"] == "Mari"


def test_editing_validates_like_adding(client, token):
    contact_id = add(client, token, MARIA).json()["id"]

    assert edit(client, token, contact_id, contact(email="no-es-correo")).status_code == 422
    assert edit(client, token, contact_id, contact(name="")).status_code == 422
    assert edit(client, token, contact_id, contact(email="ana@example.com")).status_code == 422
    assert listing(client, token)[0]["email"] == "maria@example.com"


def test_editing_cannot_take_the_email_of_another_contact(client, token):
    add(client, token, MARIA)
    other_id = add(client, token, contact(name="Pedro", email="pedro@mail.com")).json()["id"]

    response = edit(client, token, other_id, contact(name="Pedro", email="maria@example.com"))

    assert response.status_code == 409
    assert response.json()["code"] == "contact_duplicate"
    assert listing(client, token)[1]["email"] == "pedro@mail.com"


def test_editing_an_unknown_contact_is_a_404(client, token):
    response = edit(client, token, uuid.uuid4(), MARIA)

    assert response.status_code == 404
    assert response.json()["code"] == "contact_not_found"


def test_a_malformed_contact_id_is_rejected(client, token):
    assert edit(client, token, "no-es-un-uuid", MARIA).status_code == 422
    assert remove(client, token, "no-es-un-uuid").status_code == 422


# --- Baja ---------------------------------------------------------------------------


def test_a_contact_is_deleted(client, token):
    contact_id = add(client, token, MARIA).json()["id"]

    response = remove(client, token, contact_id)

    assert response.status_code == 204
    assert response.content == b""
    assert listing(client, token) == []


def test_deleting_twice_is_a_404(client, token):
    contact_id = add(client, token, MARIA).json()["id"]
    remove(client, token, contact_id)

    response = remove(client, token, contact_id)

    assert response.status_code == 404
    assert response.json()["code"] == "contact_not_found"


# --- Cada cuenta ve solo lo suyo ----------------------------------------------------


def test_each_account_only_sees_its_own_contacts(client, token, luis_token):
    add(client, token, MARIA)

    assert listing(client, luis_token) == []


def test_two_accounts_can_have_the_same_contact(client, token, luis_token):
    assert add(client, token, MARIA).status_code == 201
    assert add(client, luis_token, MARIA).status_code == 201


def test_an_account_cannot_edit_or_delete_contacts_of_another(client, token, luis_token):
    contact_id = add(client, token, MARIA).json()["id"]

    assert edit(client, luis_token, contact_id, contact(name="Hackeado")).status_code == 404
    assert remove(client, luis_token, contact_id).status_code == 404
    assert listing(client, token)[0]["name"] == "María Gómez"


def test_deleting_the_account_deletes_its_contacts(client, db, token):
    add(client, token, MARIA)

    client.delete("/users/me", headers=bearer(token))

    assert db.scalar(select(func.count()).select_from(TrustedContact)) == 0


# --- Autenticación ------------------------------------------------------------------


def test_every_endpoint_requires_a_valid_access_token(client, token):
    contact_id = add(client, token, MARIA).json()["id"]
    invalid_token = {"Authorization": "Bearer no-es-un-token"}

    for method, path, body in [
        ("GET", "/contacts", None),
        ("POST", "/contacts", MARIA),
        ("PUT", f"/contacts/{contact_id}", MARIA),
        ("DELETE", f"/contacts/{contact_id}", None),
    ]:
        assert client.request(method, path, json=body).status_code == 401
        assert client.request(method, path, json=body, headers=invalid_token).status_code == 401


# --- Fallos de persistencia ---------------------------------------------------------


def test_a_concurrent_duplicate_at_save_time_is_a_409(client, token, monkeypatch):
    def fail(*_):
        raise IntegrityError("INSERT", {}, Exception("fallo"))

    monkeypatch.setattr(repository, "create", fail)

    response = add(client, token, MARIA)

    # El índice único lo detecta aunque la comprobación previa no lo viera.
    assert response.status_code == 409
    assert response.json()["code"] == "contact_duplicate"


def test_an_unexpected_database_error_is_a_500_and_keeps_the_list(client, token, monkeypatch):
    def fail(*_):
        raise DataError("INSERT", {}, Exception("fallo"))

    monkeypatch.setattr(repository, "create", fail)

    response = add(client, token, MARIA)

    assert response.status_code == 500
    assert response.json()["code"] == "contact_save_failed"
    assert listing(client, token) == []


def test_a_failed_edit_keeps_the_contact(client, token, monkeypatch):
    contact_id = add(client, token, MARIA).json()["id"]

    def fail(*_):
        raise DataError("UPDATE", {}, Exception("fallo"))

    monkeypatch.setattr(repository, "update", fail)

    response = edit(client, token, contact_id, contact(name="Otro"))

    assert response.status_code == 500
    assert response.json()["code"] == "contact_save_failed"
    assert listing(client, token)[0]["name"] == "María Gómez"


def test_a_failed_delete_keeps_the_contact(client, token, monkeypatch):
    contact_id = add(client, token, MARIA).json()["id"]

    def fail(*_):
        raise DataError("DELETE", {}, Exception("fallo"))

    monkeypatch.setattr(repository, "delete_owned", fail)

    response = remove(client, token, contact_id)

    assert response.status_code == 500
    assert response.json()["code"] == "contact_delete_failed"
    assert len(listing(client, token)) == 1


@pytest.mark.parametrize("operation", ["create", "update", "delete_owned"])
def test_unavailable_database_is_reported_as_503(client, token, monkeypatch, operation):
    contact_id = add(client, token, MARIA).json()["id"]

    def fail(*_):
        raise OperationalError("SQL", {}, Exception("conexión rechazada"))

    monkeypatch.setattr(repository, operation, fail)

    responses = {
        "create": lambda: add(client, token, contact(email="otro@mail.com")),
        "update": lambda: edit(client, token, contact_id, contact(name="Otro")),
        "delete_owned": lambda: remove(client, token, contact_id),
    }
    response = responses[operation]()

    assert response.status_code == 503
    assert response.json()["code"] == "database_unavailable"
