import pytest
from pydantic import ValidationError

from app.modules.places.schemas import ActiveRouteUpdate, RouteStatus
from app.modules.users.schemas import HapticEvent, PreferencesUpdate, UserCreate
from app.modules.voice.schemas import VoiceCommandRequest


def test_user_create_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(email="no-es-correo", password="clave-segura-1")


def test_user_create_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreate(email="ana@example.com", password="corta")


def test_voice_command_requires_text():
    with pytest.raises(ValidationError):
        VoiceCommandRequest(text="")


def test_route_status_enum_rejects_unknown_value():
    assert ActiveRouteUpdate(status="paused").status is RouteStatus.PAUSED
    with pytest.raises(ValidationError):
        ActiveRouteUpdate(status="volando")


def test_preferences_defaults_match_the_phone():
    preferences = PreferencesUpdate()

    assert (preferences.voice_language, preferences.speech_rate) == ("es-MX", 1.0)
    assert preferences.haptics_enabled is True
    assert preferences.haptic_intensity == "medium"
    assert preferences.haptic_disabled_events == []


@pytest.mark.parametrize(
    "field",
    [
        {"speech_rate": 0.25},
        {"speech_rate": 2.5},
        {"voice_language": "en-US"},
        {"voice_language": "es"},
        {"haptic_intensity": "max"},
        {"haptic_disabled_events": ["criticalAlert"]},
        {"haptic_disabled_events": ["emergencySent"]},
    ],
)
def test_preferences_reject_values_the_phone_does_not_allow(field):
    with pytest.raises(ValidationError):
        PreferencesUpdate(**field)


def test_preferences_accept_spanish_variants_and_dedupe_events():
    preferences = PreferencesUpdate(
        voice_language="es-419",
        haptic_disabled_events=["routeFinished", "routeReady", "routeFinished"],
    )

    assert preferences.voice_language == "es-419"
    assert preferences.haptic_disabled_events == [
        HapticEvent.ROUTE_FINISHED,
        HapticEvent.ROUTE_READY,
    ]


def test_preferences_accept_turn_haptic_events():
    # Guiar Giros (SCRUM-312): izquierda y derecha vibran distinto y se pueden apagar.
    preferences = PreferencesUpdate(haptic_disabled_events=["turnRight", "turnLeft", "routeReady"])

    assert preferences.haptic_disabled_events == [
        HapticEvent.ROUTE_READY,
        HapticEvent.TURN_LEFT,
        HapticEvent.TURN_RIGHT,
    ]


def test_preferences_accept_narration_haptic_events():
    # Disponibilidad de la Narración (SCRUM-41): la caída y la vuelta vibran y se pueden apagar.
    preferences = PreferencesUpdate(
        haptic_disabled_events=["narrationAvailable", "narrationUnavailable"]
    )

    assert set(preferences.haptic_disabled_events) == {
        HapticEvent.NARRATION_UNAVAILABLE,
        HapticEvent.NARRATION_AVAILABLE,
    }
