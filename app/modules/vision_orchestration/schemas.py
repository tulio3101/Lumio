from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AlertLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"


class FrameSubmission(BaseModel):
    frame_base64: str = Field(
        description="Frame comprimido (JPEG) codificado en base64. No se persiste."
    )
    captured_at: datetime
    location: GeoPoint | None = None
    consent_given: bool = Field(description="El usuario consintió el envío de imágenes.")
    consent_version: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        description=(
            "Versión del aviso de privacidad que aceptó el usuario (SCRUM-324). Sin ella la "
            "solicitud se rechaza con 403 `consent_required`."
        ),
    )


class DetectedObject(BaseModel):
    label: str
    distance_meters: float | None = Field(default=None, ge=0)


class VisionAnalysisResponse(BaseModel):
    description: str = Field(description="Descripción del entorno lista para narrar.")
    objects: list[DetectedObject] = Field(default_factory=list)
    alert_level: AlertLevel = AlertLevel.INFO
