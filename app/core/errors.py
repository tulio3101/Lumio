"""Errores de aplicación y formato común de respuesta de error.

Los módulos lanzan subclases de ``AppError``; aquí se traducen a HTTP con el cuerpo
``{"detail": <mensaje legible>, "code": <identificador estable>}``. El cliente decide
qué locutar a partir de ``code``, no del texto.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    detail: str = Field(description="Mensaje legible en español.")
    code: str = Field(description="Identificador estable del error.", examples=["not_found"])


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    message: str = "Error interno del servidor."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class ServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "database_unavailable"
    message = "El servicio de persistencia no está disponible. Intenta de nuevo."


def _error_response(error: AppError) -> JSONResponse:
    body = ErrorResponse(detail=error.message, code=error.code)
    return JSONResponse(status_code=error.status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc)

    @app.exception_handler(OperationalError)
    async def handle_database_unavailable(_: Request, exc: OperationalError) -> JSONResponse:
        logger.exception("Base de datos no disponible", exc_info=exc)
        return _error_response(ServiceUnavailableError())
