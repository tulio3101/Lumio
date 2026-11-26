from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valor de ejemplo del repo (público): nunca debe firmar tokens fuera de local.
INSECURE_JWT_SECRET = "change-me"
MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Lumio API"
    environment: Literal["local", "dev", "prod"] = "local"
    debug: bool = False

    database_url: str = "postgresql+psycopg://lumio:lumio@localhost:5432/lumio"

    jwt_secret: str = INSECURE_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 30

    # Correo (alertas de emergencia). «log» solo escribe el correo en los logs y únicamente
    # sirve en local; en dev y prod hay que usar «ses» (ADR-310).
    email_backend: Literal["log", "ses"] = "log"
    ses_sender_email: str | None = None
    aws_region: str = "us-east-1"

    # Narración del entorno (SCRUM-38, ADR-308). «bedrock» llama al VLM con el perfil de
    # inferencia «us.» (procesamiento solo en EE. UU.); «fake» devuelve un texto fijo para
    # probar la app sin AWS y solo vale en local; «disabled» responde 503 narration_unavailable.
    narration_backend: Literal["disabled", "fake", "bedrock"] = "disabled"
    narration_model_id: str = "us.anthropic.claude-haiku-5-5"
    # Si Bedrock tarda más, se responde 504: la app descarta lo que llegue más de 4 s
    # después de capturar la foto.
    narration_timeout_seconds: float = 4.0
    # Límite por usuario (en memoria, por proceso, como el resto del rate limiting de ADR-310).
    narration_min_interval_seconds: float = 3.0
    narration_daily_limit: int = 1500

    @model_validator(mode="after")
    def _fake_narration_only_in_local(self) -> Self:
        if self.narration_backend == "fake" and self.environment != "local":
            raise ValueError("NARRATION_BACKEND=fake solo se permite con ENVIRONMENT=local.")
        return self

    @model_validator(mode="after")
    def _require_a_sender_for_ses(self) -> Self:
        if self.email_backend == "ses" and not self.ses_sender_email:
            raise ValueError("SES_SENDER_EMAIL es obligatorio cuando EMAIL_BACKEND=ses.")
        return self

    @model_validator(mode="after")
    def _require_strong_jwt_secret_outside_local(self) -> Self:
        if self.environment == "local":
            return self
        if self.jwt_secret == INSECURE_JWT_SECRET or len(self.jwt_secret) < MIN_JWT_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET debe ser un valor aleatorio de al menos {MIN_JWT_SECRET_LENGTH} "
                f"caracteres cuando ENVIRONMENT={self.environment}."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
