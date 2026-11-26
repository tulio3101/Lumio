from enum import StrEnum

from pydantic import BaseModel, Field


class VoiceIntent(StrEnum):
    START_ROUTE = "start_route"
    STOP_ROUTE = "stop_route"
    DESCRIBE_SURROUNDINGS = "describe_surroundings"
    REPEAT = "repeat"
    UNKNOWN = "unknown"


class VoiceCommandRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=500,
        description="Comando transcrito por el cliente.",
        examples=["llévame a la farmacia"],
    )
    language: str = Field(default="es", description="Código de idioma ISO 639-1.")


class VoiceCommandResponse(BaseModel):
    intent: VoiceIntent
    parameters: dict[str, str] = Field(
        default_factory=dict, description="Parámetros extraídos del comando."
    )
    spoken_reply: str = Field(description="Texto que el cliente debe locutar al usuario.")
