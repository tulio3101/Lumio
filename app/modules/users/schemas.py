import re
import unicodedata
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

DISPLAY_NAME_MAX_LENGTH = 60
# Letras (con tildes y ñ), espacios, apóstrofo (recto o tipográfico), punto y guion.
_NAME_SYMBOLS = frozenset(" '’.-")
# Celular colombiano sin prefijo: 10 dígitos que empiezan por 3.
_PHONE = re.compile(r"3\d{9}")
# Separadores que se aceptan al escribir el número y se quitan al guardar.
_PHONE_SEPARATORS = re.compile(r"[\s-]")


class UserCreate(BaseModel):
    email: EmailStr = Field(
        description="Correo electrónico de la cuenta.", examples=["ana@example.com"]
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Contraseña en texto plano; se almacena solo como hash.",
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(description="ID token emitido por Google al cliente.")


class RefreshRequest(BaseModel):
    refresh_token: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str | None = Field(
        default=None, description="Nombre para mostrar; null si no lo ha puesto."
    )
    phone: str | None = Field(
        default=None,
        description="Celular colombiano de 10 dígitos sin prefijo; null si no lo ha puesto.",
        examples=["3001234567"],
    )
    created_at: datetime


def normalize_display_name(value: str | None) -> str | None:
    """Recorta y une los espacios; vacío equivale a quitar el nombre."""
    if value is None:
        return None
    # NFC: «á» escrita como «a» + tilde combinante cuenta como una sola letra.
    name = " ".join(unicodedata.normalize("NFC", value).split())
    if not name:
        return None
    if len(name) > DISPLAY_NAME_MAX_LENGTH:
        raise ValueError(f"El nombre puede tener como máximo {DISPLAY_NAME_MAX_LENGTH} caracteres.")
    if not any(char.isalpha() for char in name) or not all(
        char.isalpha() or char in _NAME_SYMBOLS for char in name
    ):
        raise ValueError(
            "El nombre solo puede tener letras, espacios, apóstrofos, puntos y guiones."
        )
    return name


def normalize_phone(value: str | None) -> str | None:
    """Quita espacios y guiones; vacío equivale a quitar el celular."""
    if value is None:
        return None
    phone = _PHONE_SEPARATORS.sub("", value)
    if not phone:
        return None
    if not _PHONE.fullmatch(phone):
        raise ValueError("El celular debe tener 10 dígitos y empezar por 3.")
    return phone


class UserProfileUpdate(BaseModel):
    """Cambios parciales del perfil: solo se modifican los campos enviados. Enviar null
    o una cadena vacía quita el dato. El correo no se puede cambiar."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(
        default=None,
        max_length=200,
        description=(
            "Nombre para mostrar: 1 a 60 caracteres tras recortar espacios; letras, "
            "espacios, apóstrofos, puntos y guiones."
        ),
        examples=["Ana María Pérez"],
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="Celular colombiano: 10 dígitos que empiezan por 3. Admite espacios y guiones.",
        examples=["300 123 4567"],
    )

    _normalize_display_name = field_validator("display_name")(normalize_display_name)
    _normalize_phone = field_validator("phone")(normalize_phone)


SPEECH_RATE_MIN = 0.5
SPEECH_RATE_MAX = 2.0
# Variante de español en BCP-47: es-MX, es-ES, es-419…
_VOICE_LANGUAGE = r"^es-(?:[A-Z]{2}|419)$"


class HapticIntensity(StrEnum):
    SOFT = "soft"
    MEDIUM = "medium"
    STRONG = "strong"


class HapticEvent(StrEnum):
    """Eventos que el usuario puede apagar. Las alertas críticas y las del botón de
    emergencia vibran siempre y no se aceptan aquí."""

    ROUTE_READY = "routeReady"
    ROUTE_FAILED = "routeFailed"
    ROUTE_FINISHED = "routeFinished"
    # Guiar Giros (SCRUM-312): un patrón distinto para cada lado.
    TURN_LEFT = "turnLeft"
    TURN_RIGHT = "turnRight"


class PreferencesUpdate(BaseModel):
    """Preferencias completas de voz y vibración: siempre se envían todas (reemplazo).
    Mismas reglas que en el teléfono."""

    model_config = ConfigDict(extra="forbid")

    voice_language: str = Field(
        default="es-MX",
        pattern=_VOICE_LANGUAGE,
        description="Variante de español de la voz (BCP-47).",
        examples=["es-MX"],
    )
    voice_identifier: str | None = Field(
        default=None,
        max_length=255,
        description="Voz del sistema elegida; null usa la predeterminada del idioma.",
    )
    speech_rate: float = Field(
        default=1.0,
        ge=SPEECH_RATE_MIN,
        le=SPEECH_RATE_MAX,
        description="Veces la velocidad normal: de 0,5 a 2.",
        examples=[1.25],
    )
    haptics_enabled: bool = Field(default=True, description="Vibración de los eventos de ruta.")
    haptic_intensity: HapticIntensity = Field(default=HapticIntensity.MEDIUM)
    haptic_disabled_events: list[HapticEvent] = Field(
        default_factory=list,
        max_length=len(HapticEvent),
        description="Eventos de ruta que no vibran. Las alertas de seguridad no se pueden apagar.",
    )

    @field_validator("haptic_disabled_events")
    @classmethod
    def _unique_events(cls, events: list[HapticEvent]) -> list[HapticEvent]:
        # Sin repetidos y en un orden estable.
        return sorted(set(events))


class PreferencesRead(PreferencesUpdate):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    updated_at: datetime | None = Field(
        default=None,
        description="Cuándo se guardaron; null si la cuenta nunca guardó preferencias.",
    )


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(
        description="Correo de la cuenta con contraseña propia.", examples=["ana@example.com"]
    )


class PasswordResetAccepted(BaseModel):
    message: str = Field(
        default=(
            "Si el correo corresponde a una cuenta con contraseña, te enviamos un código. "
            "Revisa tu correo."
        ),
        description="Siempre el mismo texto: no revela si la cuenta existe.",
    )


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str = Field(
        pattern=r"^\d{6}$",
        description="Código de 6 dígitos recibido por correo.",
        examples=["482915"],
    )
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="Nueva contraseña; mismas reglas que al crear la cuenta.",
    )


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=128, description="Contraseña actual.")
    new_password: str = Field(
        min_length=8,
        max_length=128,
        description="Nueva contraseña; mismas reglas que al crear la cuenta.",
    )


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = Field(default="bearer")
    expires_in: int = Field(description="Segundos de vigencia del access token.", examples=[900])
