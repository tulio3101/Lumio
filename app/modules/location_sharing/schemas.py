import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Position(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90, examples=[4.6097])
    longitude: float = Field(ge=-180, le=180, examples=[-74.0817])
    accuracy_m: float | None = Field(
        default=None, ge=0, le=100_000, description="Precisión de la ubicación en metros."
    )


class LocationShareStart(Position):
    duration_minutes: int = Field(
        default=60,
        ge=15,
        le=240,
        description="Cuánto dura como máximo; después deja de compartirse solo.",
    )


class LocationShareRead(BaseModel):
    id: uuid.UUID
    expires_at: datetime
    contacts_total: int
    contacts_sent: int = Field(description="Contactos a los que llegó el correo con el enlace.")
