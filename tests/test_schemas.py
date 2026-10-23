import pytest
from pydantic import ValidationError

from app.modules.narration.schemas import NarrationRequest
from app.modules.places.schemas import ActiveRouteUpdate, RouteStatus
from app.modules.users.schemas import UserCreate
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


def test_narration_defaults():
    request = NarrationRequest(context="Hay una puerta a la derecha")

    assert request.language == "es"
    assert request.priority == "normal"


def test_route_status_enum_rejects_unknown_value():
    assert ActiveRouteUpdate(status="paused").status is RouteStatus.PAUSED
    with pytest.raises(ValidationError):
        ActiveRouteUpdate(status="volando")
