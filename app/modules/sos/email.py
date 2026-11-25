"""Envío del correo de emergencia: SES en dev y prod, solo logs en local (ADR-310)."""

import logging
from functools import lru_cache
from typing import Annotated, Protocol

from fastapi import Depends

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """El correo no salió: servicio caído, remitente no verificado o correo rechazado."""


class EmailSender(Protocol):
    def send(self, *, to: str, subject: str, body: str) -> None:
        """Envía un correo de texto plano o lanza EmailDeliveryError."""


class LogEmailSender:
    """Solo en local: escribe el correo en los logs en lugar de enviarlo."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("Correo (no enviado, EMAIL_BACKEND=log) a %s: %s\n%s", to, subject, body)


class UnconfiguredEmailSender:
    """Fuera de local sin SES configurado. Falla a propósito: una alerta de emergencia que
    parece enviada y no sale es peor que un error claro."""

    def send(self, *, to: str, subject: str, body: str) -> None:
        raise EmailDeliveryError("El envío de correo no está configurado (EMAIL_BACKEND=ses).")


class SesEmailSender:
    def __init__(self, sender: str, region: str) -> None:
        self._sender = sender
        self._region = region
        self._client = None

    def _ses(self):  # noqa: ANN202 - el cliente de boto3 no tiene tipo estático
        if self._client is None:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "sesv2",
                region_name=self._region,
                config=Config(
                    retries={"max_attempts": 3, "mode": "standard"},
                    connect_timeout=5,
                    read_timeout=10,
                ),
            )
        return self._client

    def send(self, *, to: str, subject: str, body: str) -> None:
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            self._ses().send_email(
                FromEmailAddress=self._sender,
                Destination={"ToAddresses": [to]},
                Content={
                    "Simple": {
                        "Subject": {"Data": subject, "Charset": "UTF-8"},
                        "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                    }
                },
            )
        except (BotoCoreError, ClientError) as exc:
            raise EmailDeliveryError(str(exc)) from exc


@lru_cache
def get_email_sender() -> EmailSender:
    settings = get_settings()
    if settings.email_backend == "ses" and settings.ses_sender_email:
        return SesEmailSender(settings.ses_sender_email, settings.aws_region)
    if settings.environment == "local":
        return LogEmailSender()
    return UnconfiguredEmailSender()


EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]
