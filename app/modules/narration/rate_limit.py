"""Control de costo del VLM (ADR-308 §4): por usuario, 1 solicitud cada 3 s y 1.500 al día.

En memoria y por proceso, igual que el resto del rate limiting de ADR-310. Con varios workers
el límite efectivo se multiplica por su número; sigue acotando el costo, que es lo que importa.
"""

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings


@dataclass
class _Usage:
    last_at: float
    day: date
    count: int


class NarrationRateLimiter:
    def __init__(
        self,
        min_interval_seconds: float,
        daily_limit: int,
        clock: Callable[[], float] = time.monotonic,
        today: Callable[[], date] = lambda: datetime.now(UTC).date(),
    ) -> None:
        self._min_interval = min_interval_seconds
        self._daily_limit = daily_limit
        self._clock = clock
        self._today = today
        self._usage: dict[uuid.UUID, _Usage] = {}
        self._lock = threading.Lock()

    def try_acquire(self, user_id: uuid.UUID) -> bool:
        """True y cuenta la solicitud si está dentro de los límites; False si no."""
        now, today = self._clock(), self._today()
        with self._lock:
            usage = self._usage.get(user_id)
            if usage is None or usage.day != today:
                self._usage[user_id] = _Usage(last_at=now, day=today, count=1)
                return True
            if now - usage.last_at < self._min_interval or usage.count >= self._daily_limit:
                return False
            usage.last_at = now
            usage.count += 1
            return True


@lru_cache
def get_rate_limiter() -> NarrationRateLimiter:
    settings = get_settings()
    return NarrationRateLimiter(
        settings.narration_min_interval_seconds, settings.narration_daily_limit
    )


NarrationRateLimiterDep = Annotated[NarrationRateLimiter, Depends(get_rate_limiter)]
