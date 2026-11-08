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