from enum import StrEnum

from pydantic import BaseModel, Field


class NarrationTrigger(StrEnum):
    """Qué disparó la narración (ADR-308 §6). Solo para métricas de uso y costo."""

    GESTURE = "gesture"
    AUTO = "auto"


class SceneLanguage(StrEnum):
    ES = "es"


class VisionAnalysisResponse(BaseModel):
    """Descripción lista para locutar. La app la encola como P3 (`environmentInformation`).

    No trae nivel de alerta ni objetos: un riesgo nunca puede venir de la red, eso lo decide
    el loop de seguridad en el teléfono (ADR-308).
    """

    text: str = Field(description="Descripción del entorno lista para locutar (≤ 2 oraciones).")
    model: str = Field(description="Modelo que generó la descripción.")
    latency_ms: int = Field(ge=0, description="Tiempo que tardó el backend en describir la foto.")
