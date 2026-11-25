"""Preferencias de voz y vibración contra Postgres: migración 0008, copia por cuenta."""

from app.modules.users.models import UserPreferences

from .conftest import create_user, login

CHOSEN = {
    "voice_language": "es-ES",
    "voice_identifier": "com.apple.voice.compact.es-ES.Monica",
    "speech_rate": 1.25,
    "haptics_enabled": False,
    "haptic_intensity": "strong",
    "haptic_disabled_events": ["routeReady"],
}


def test_without_saved_preferences_the_defaults_are_returned(api, auth):
    response = api.get("/users/me/preferences", headers=auth)

    assert response.status_code == 200
    assert response.json() == {
        "voice_language": "es-MX",
        "voice_identifier": None,
        "speech_rate": 1.0,
        "haptics_enabled": True,
        "haptic_intensity": "medium",
        "haptic_disabled_events": [],
        "updated_at": None,
    }


def test_preferences_are_saved_and_read_back(api, session_factory, user, auth):
    saved = api.put("/users/me/preferences", json=CHOSEN, headers=auth)

    assert saved.status_code == 200
    body = saved.json()
    assert {key: body[key] for key in CHOSEN} == CHOSEN
    assert body["updated_at"] is not None
    assert api.get("/users/me/preferences", headers=auth).json() == body
    with session_factory() as session:
        stored = session.get(UserPreferences, user.id)
        assert (stored.speech_rate, stored.haptic_disabled_events) == (1.25, ["routeReady"])


def test_saving_again_replaces_the_previous_preferences(api, session_factory, user, auth):
    api.put("/users/me/preferences", json=CHOSEN, headers=auth)

    response = api.put("/users/me/preferences", json={**CHOSEN, "speech_rate": 0.75}, headers=auth)

    assert response.status_code == 200
    assert response.json()["speech_rate"] == 0.75
    with session_factory() as session:
        assert session.get(UserPreferences, user.id).speech_rate == 0.75


def test_invalid_preferences_do_not_touch_the_database(api, session_factory, user, auth):
    api.put("/users/me/preferences", json=CHOSEN, headers=auth)

    for invalid in (
        {**CHOSEN, "speech_rate": 3},
        {**CHOSEN, "voice_language": "en-US"},
        {**CHOSEN, "haptic_intensity": "max"},
        {**CHOSEN, "haptic_disabled_events": ["criticalAlert"]},
        {**CHOSEN, "unknown": True},
    ):
        assert api.put("/users/me/preferences", json=invalid, headers=auth).status_code == 422

    with session_factory() as session:
        assert session.get(UserPreferences, user.id).speech_rate == 1.25


def test_preferences_require_a_session(api):
    assert api.get("/users/me/preferences").status_code == 401
    assert api.put("/users/me/preferences", json=CHOSEN).status_code == 401


def test_each_account_has_its_own_preferences(api, session_factory, auth):
    luis = create_user(session_factory, "luis@example.com")
    luis_auth = login(api, luis.email)

    api.put("/users/me/preferences", json=CHOSEN, headers=auth)

    assert api.get("/users/me/preferences", headers=luis_auth).json()["updated_at"] is None


def test_deleting_the_account_deletes_its_preferences(api, session_factory, user, auth):
    api.put("/users/me/preferences", json=CHOSEN, headers=auth)

    assert api.delete("/users/me", headers=auth).status_code == 204

    with session_factory() as session:
        assert session.get(UserPreferences, user.id) is None
