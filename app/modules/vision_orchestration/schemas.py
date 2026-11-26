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


class NarrationStatusReason(StrEnum):
    """Por qué la narración está o no disponible (SCRUM-41)."""

    AVAILABLE = "available"
    NOT_CONFIGURED = "not_configured"
    DEGRADED = "degraded"


class NarrationStatusResponse(BaseModel):
    """Estado de la narración para que la app decida si envía fotos (SCRUM-41)."""

    available: bool = Field(description="true si vale la pena pedir una descripción ahora.")
    reason: NarrationStatusReason = Field(
        description=(
            "`available`; `not_configured` (el VLM está apagado en este entorno) o `degraded` "
            "(el VLM falló varias veces seguidas)."
        )
    )
    retry_after_seconds: int | None = Field(
        default=None,
        ge=1,
        description="Solo con `degraded`: cuándo conviene volver a consultar.",
    )
