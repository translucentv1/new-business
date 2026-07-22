"""
Exponential Backoff mit Jitter.

Sollte trotz Rate-Limiting ein 429 auftauchen, wird mit
steigender Wartezeit (1s, 2s, 4s, 8s, …) + zufälligem Jitter
wiederholt, damit nicht alle wartenden Clients gleichzeitig
erneut anfragen.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class RetryState:
    """Zustand für eine Retry-Sequenz."""

    attempt: int = 0
    max_attempts: int = 5
    base_delay: float = 1.0  # Sekunden
    max_delay: float = 30.0
    jitter_factor: float = 0.25  # ±25 % Jitter

    def reset(self) -> None:
        self.attempt = 0

    def next_delay(self) -> float:
        """
        Berechnet die nächste Wartezeit mit vollem Jitter.

        Formel: delay = min(base * 2^attempt, max_delay)
                jitter = delay * random.uniform(-jitter_factor, +jitter_factor)
        """
        self.attempt += 1
        delay = min(self.base_delay * (2 ** (self.attempt - 1)), self.max_delay)
        jitter = delay * self.jitter_factor
        return delay + random.uniform(-jitter, jitter)

    @property
    def is_exhausted(self) -> bool:
        return self.attempt >= self.max_attempts

    @property
    def remaining(self) -> int:
        return max(0, self.max_attempts - self.attempt)


class ExponentialBackoff:
    """
    Retry-Loop mit exponentiellem Backoff + Jitter.

    Usage:
        backoff = ExponentialBackoff()
        result = await backoff.run(coro_factory)  # coro_factory: async () -> response
    """

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter_factor: float = 0.25,
        should_retry: Optional[Callable[[Exception], bool]] = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor
        self._should_retry = should_retry or self._default_should_retry

    @staticmethod
    def _default_should_retry(exc: Exception) -> bool:
        """Standard: nur 429 und 5xx (Server-Fehler) wiederholen."""
        status = getattr(exc, "status", None) or getattr(exc, "code", None)
        if status is not None:
            return status in (429, 500, 502, 503, 504)
        # Timeout / Netzwerkfehler
        return isinstance(exc, (asyncio.TimeoutError, ConnectionError))

    async def run(self, coro_factory: Callable, *args, **kwargs):
        """
        Führt coro_factory(*args, **kwargs) aus und wiederholt bei Fehlschlag.

        Args:
            coro_factory: Muss ein Callable sein, das eine Awaitable liefert.
                          (z. B. lambda: client.chat(...))

        Returns:
            Ergebnis des erfolgreichen Aufrufs.

        Raises:
            Letzte Exception, wenn alle Versuche erschöpft sind.
        """
        state = RetryState(
            max_attempts=self.max_attempts,
            base_delay=self.base_delay,
            max_delay=self.max_delay,
            jitter_factor=self.jitter_factor,
        )
        last_exc: Optional[Exception] = None

        while not state.is_exhausted:
            try:
                return await coro_factory(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if not self._should_retry(e):
                    raise  # Nicht-wiederholbare Fehler sofort durchlassen

                delay = state.next_delay()

                # Bei 429 den Retry-After-Header nutzen, falls vorhanden
                retry_after = getattr(e, "retry_after", None)
                if retry_after is not None:
                    delay = max(delay, float(retry_after))

                await asyncio.sleep(delay)

        raise last_exc or RuntimeError("Retry erschöpft (kein letzter Fehler)")