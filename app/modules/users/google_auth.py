"""Verificación del ID token de Google (Iniciar sesión / Crear cuenta con Google).

La app obtiene el ID token con el SDK de Google y lo envía al backend, que comprueba la firma
contra las llaves públicas de Google, el emisor, la vigencia y que la audiencia sea uno de
nuestros client ID (GOOGLE_CLIENT_IDS). Sin client ID configurado, el inicio con Google
responde 503 en lugar de aceptar tokens emitidos para otras apps.
"""

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Protocol

from fastapi import Depends

from app.core.config import get_settings

logger = logging.getLogger(__name__)

GOOGLE_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str
    email: str | None
    email_verified: bool


class InvalidGoogleToken(Exception):
    """Token mal formado, vencido, con firma o audiencia incorrecta, o de otro emisor."""


class GoogleAuthUnavailable(Exception):
    """Sin client ID configurado o sin poder descargar las llaves públicas de Google."""


class GoogleTokenVerifier(Protocol):
    def verify(self, token: str) -> GoogleIdentity:
        """Devuelve la identidad del token o lanza InvalidGoogleToken / GoogleAuthUnavailable."""


class UnconfiguredGoogleVerifier:
    def verify(self, token: str) -> GoogleIdentity:
        raise GoogleAuthUnavailable("GOOGLE_CLIENT_IDS no está configurado.")


class GoogleIdTokenVerifier:
    def __init__(self, client_ids: list[str]) -> None:
        self._client_ids = client_ids
        self._request = None

    def _transport(self):  # noqa: ANN202 - tipos de google-auth
        if self._request is None:
            import urllib3
            from google.auth.transport.urllib3 import Request

            self._request = Request(urllib3.PoolManager(timeout=urllib3.Timeout(5.0)))
        return self._request

    def verify(self, token: str) -> GoogleIdentity:
        from google.auth.exceptions import GoogleAuthError, TransportError
        from google.oauth2 import id_token

        try:
            claims = id_token.verify_oauth2_token(
                token, self._transport(), audience=self._client_ids, clock_skew_in_seconds=10
            )
        except TransportError as exc:
            logger.warning("No se pudieron obtener las llaves de Google: %s", exc)
            raise GoogleAuthUnavailable(str(exc)) from exc
        except (ValueError, GoogleAuthError) as exc:
            # Firma, audiencia o vigencia: ValueError; emisor incorrecto: GoogleAuthError.
            raise InvalidGoogleToken(str(exc)) from exc
        return identity_from_claims(claims)


def identity_from_claims(claims: dict) -> GoogleIdentity:
    """Valida los claims ya verificados por firma y extrae la identidad."""
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise InvalidGoogleToken("Emisor desconocido.")
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise InvalidGoogleToken("El token no trae sub.")
    email = claims.get("email")
    # Google manda email_verified como booleano, y en tokens antiguos como texto.
    verified = claims.get("email_verified") in (True, "true")
    return GoogleIdentity(
        sub=sub, email=email if isinstance(email, str) else None, email_verified=verified
    )


@lru_cache
def get_google_verifier() -> GoogleTokenVerifier:
    client_ids = get_settings().google_client_ids
    if not client_ids:
        return UnconfiguredGoogleVerifier()
    return GoogleIdTokenVerifier(client_ids)


GoogleVerifierDep = Annotated[GoogleTokenVerifier, Depends(get_google_verifier)]
