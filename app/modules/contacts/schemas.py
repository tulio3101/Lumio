import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.modules.users.schemas import normalize_display_name


def normalize_contact_name(value: str) -> str:
    """Mismas reglas que el nombre de la cuenta, pero aquí es obligatorio."""
    name = normalize_display_name(value)
    if name is None:
        raise ValueError("Escribe el nombre del contacto.")
    return name


class TrustedContactWrite(BaseModel):
    """Cuerpo de crear y de editar un contacto: siempre los dos campos."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        max_length=200,
        description=(
            "Nombre del contacto: 1 a 60 caracteres tras recortar espacios; letras, "
            "espacios, apóstrofos, puntos y guiones."
        ),
        examples=["María Gómez"],
    )
    email: EmailStr = Field(
        max_length=320,
        description="Correo del contacto. Se guarda sin espacios laterales y en minúsculas.",
        examples=["maria@example.com"],
    )

    _normalize_name = field_validator("name")(normalize_contact_name)

    @field_validator("email", mode="before")
    @classmethod
    def _strip_email(cls, value: object) -> object:
        # El teclado del teléfono suele dejar un espacio al final al autocompletar.
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, value: str) -> str:
        return value.lower()


class TrustedContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    created_at: datetime
