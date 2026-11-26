"""Disponibilidad de la narración (SCRUM-41).

El VLM puede estar sin configurar o fallar varias veces seguidas (throttling de Bedrock, error
del servicio, timeouts). La app consulta `GET /vision/status` para saber si vale la pena enviar
fotos y avisar al usuario cuando la narración se cae o vuelve, sin gastar una foto en probarlo.

Tras `failure_threshold` fallas seguidas la narración se marca «degradada» durante
`cooldown_seconds` desde la última falla. Pasado ese tiempo vuelve a anunciarse disponible para
que la siguiente solicitud lo compruebe: si falla otra vez, sigue degradada; si funciona, se
reinicia el conteo. En memoria y por proceso, igual que el rate limiting (ADR-310).

Nada de esto guarda la foto ni el texto: solo cuenta resultados.
"""

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

FAILURE_THRESHOLD = 3
COOLDOWN_SECONDS = 30.0


@dataclass(frozen=True)
class AvailabilitySnapshot:
    degraded: bool
    retry_after_seconds: int | None = None


class NarrationAvailability:
    def __init__(
        self,
        failure_threshold: int = FAILURE_THRESHOLD,
        cooldown_seconds: float = COOLDOWN_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._threshold = failure_threshold
        self._cooldown = cooldown_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._consecutive_failures = 0
        self._last_failure_at: float | None = None

    def record_success(self) -> None:
        with self._lock:
            self._consecutive_failures = 0
            self._last_failure_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._consecutive_failures += 1
            self._last_failure_at = self._clock()

    def snapshot(self) -> AvailabilitySnapshot:
        with self._lock:
            if self._consecutive_failures < self._threshold or self._last_failure_at is None:
                return AvailabilitySnapshot(degraded=False)
            remaining = self._cooldown - (self._clock() - self._last_failure_at)
            if remaining <= 0:
                return AvailabilitySnapshot(degraded=False)
            return AvailabilitySnapshot(degraded=True, retry_after_seconds=max(1, round(remaining)))


@lru_cache
def get_narration_availability() -> NarrationAvailability:
    return NarrationAvailability()


NarrationAvailabilityDep = Annotated[NarrationAvailability, Depends(get_narration_availability)]
