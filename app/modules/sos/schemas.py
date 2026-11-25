import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SosRequest(BaseModel):
    """Activación de la emergencia. Sin ubicación se envía igual, avisando que falta."""

    model_config = ConfigDict(extra="forbid")

    idempotency_key: uuid.UUID = Field(
        description=(
            "La genera la app al activar la emergencia. Reenviar la misma llave (por ejemplo "
            "tras perder la respuesta) no manda correos otra vez."
        ),
    )
    latitude: float | None = Field(default=None, ge=-90, le=90, examples=[4.6097])
    longitude: float | None = Field(default=None, ge=-180, le=180, examples=[-74.0817])
    accuracy_m: float | None = Field(
        default=None, ge=0, le=100_000, description="Precisión de la ubicación en metros."
    )

    @model_validator(mode="after")
    def _location_is_complete(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Envía la latitud y la longitud juntas, o ninguna.")
        if self.latitude is None and self.accuracy_m is not None:
            raise ValueError("La precisión solo tiene sentido con una ubicación.")
        return self


class SosRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str = Field(description="`sent` (todos), `partial` (algunos) o `failed` (ninguno).")
    contacts_total: int
    contacts_sent: int
    location_included: bool = Field(description="El correo llevó la ubicación.")
    created_at: datetime
