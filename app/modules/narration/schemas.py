from enum import StrEnum

from pydantic import BaseModel, Field


class NarrationPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    URGENT = "urgent"


class NarrationRequest(BaseModel):
    context: str = Field(min_length=1, description="Descripción o evento a convertir en narración.")
    language: str = Field(default="es", description="Código de idioma ISO 639-1.")
    priority: NarrationPriority = NarrationPriority.NORMAL


class NarrationResponse(BaseModel):
    text: str = Field(description="Texto final a locutar.")
    language: str
    priority: NarrationPriority
