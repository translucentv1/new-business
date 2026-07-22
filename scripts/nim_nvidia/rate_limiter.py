"""
Rate-Limiter — pro Modell separate Token-Bucket- und Sliding-Window-Limiter.

Jeder ModelEndpoint bekommt seinen eigenen Limiter mit:
  - Token-Bucket:  refill_rate = rpm / 60 Tokens pro Sekunde,
                   burst_capacity = rpm
  - Sliding-Window: optional als zweite Absicherung

Ziel: 35 RPM (unter dem 40er-NVIDIA-Limit), 429-Fehler proaktiv vermeiden.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenBucket:
    """
    Token-Bucket-Rate-Limiter.

    - tokens: Anzahl aktuell verfügbarer Tokens.
    - max_tokens: maximale Kapazität (Burst-Limit).
    - refill_rate: Tokens pro Sekunde.
    - last_refill: letzter Refill-Zeitstempel.
    """

    max_tokens: float
    refill_rate: float  # Tokens pro Sekunde
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self):
        self.tokens = self.max_tokens
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        """Füllt Tokens gemäß vergangener Zeit nach."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def acquire(self, cost: float = 1.0) -> float:
        """
        Versucht, 'cost' Tokens zu nehmen.
        Gibt 0.0 zurück bei Erfolg, positive Sekunden (Wartezeit) bei Mangel.
        """
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return 0.0
        # Wartezeit = Fehlende Tokens / Refill-Rate
        deficit = cost - self.tokens
        return deficit / self.refill_rate

    async def wait(self, cost: float = 1.0) -> None:
        """Blockiert asynchron bis genug Tokens da sind, nimmt dann cost."""
        wait_time = self.acquire(cost)
        while wait_time > 0:
            await asyncio.sleep(wait_time)
            wait_time = self.acquire(cost)


@dataclass
class SlidingWindowLimiter:
    """
    Sliding-Window-Limiter (optional, zweite Absicherung).

    Zählt Requests in einem gleitenden Zeitfenster (z. B. 60s).
    """

    max_requests: int  # Max Requests im Fenster
    window_seconds: float = 60.0
    _timestamps: deque = field(default_factory=deque)

    def _trim(self) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    def allow(self) -> bool:
        """Prüft, ob ein Request im Fenster erlaubt ist."""
        self._trim()
        return len(self._timestamps) < self.max_requests

    def record(self) -> None:
        """Zeichnet einen Request im Fenster auf."""
        self._timestamps.append(time.monotonic())

    async def wait_if_needed(self) -> None:
        """Wartet asynchron, bis ein Slot im Fenster frei ist."""
        while not self.allow():
            # Nächste Freigabe: ältester Timestamp + window_seconds
            if self._timestamps:
                wait = (self._timestamps[0] + self.window_seconds) - time.monotonic()
                if wait > 0:
                    await asyncio.sleep(wait)
            else:
                break


class RateLimiter(ABC):
    """Abstrakter Rate-Limiter — fasst TokenBucket + optional SlidingWindow."""

    @abstractmethod
    async def acquire(self) -> None:
        """Wartet asynchron, bis ein Request ausgeführt werden darf."""
        ...

    @abstractmethod
    def get_wait_estimate(self) -> float:
        """Geschätzte Wartezeit in Sekunden für den nächsten Request."""
        ...


@dataclass
class PerModelLimiter(RateLimiter):
    """
    Konkreter Rate-Limiter für ein einzelnes Modell.

    Nutzt TokenBucket (primär) + optional SlidingWindow (sekundär).
    """

    rpm: int
    bucket: TokenBucket = field(init=False)
    window: Optional[SlidingWindowLimiter] = None

    def __post_init__(self):
        self.bucket = TokenBucket(
            max_tokens=float(self.rpm),
            refill_rate=self.rpm / 60.0,
        )
        # SlidingWindow nur optional (default: None)
        # TokenBucket allein reicht für proaktives Drosseln.
        self.window = None

    async def acquire(self) -> None:
        """Wartet auf TokenBucket + SlidingWindow."""
        # 1) SlidingWindow (grobe Freigabe im Fenster)
        if self.window:
            await self.window.wait_if_needed()

        # 2) TokenBucket (feinkörnige Drosselung)
        await self.bucket.wait(cost=1.0)

        # 3) Request im Fenster vermerken
        if self.window:
            self.window.record()

    def get_wait_estimate(self) -> float:
        """Geschätzte Wartezeit für den nächsten Request."""
        wait = self.bucket.acquire(1.0)
        if wait > 0:
            return wait
        if self.window and not self.window.allow():
            return 1.0
        return 0.0


class MultiModelRateLimiter:
    """
    Verwaltet einen PerModelLimiter pro ModelEndpoint.

    Usage:
        limiter = MultiModelRateLimiter(router.endpoints)
        await limiter.acquire("deepseek-v4-pro")
    """

    def __init__(self, endpoints: list):
        self._limiters: dict[str, PerModelLimiter] = {}
        for ep in endpoints:
            self._limiters[ep.name] = PerModelLimiter(rpm=ep.rpm_limit)

    def get_limiter(self, model_name: str) -> PerModelLimiter:
        """Liefert den Limiter für ein Modell (erzeugt Default bei Unbekannt)."""
        if model_name not in self._limiters:
            self._limiters[model_name] = PerModelLimiter(rpm=35)
        return self._limiters[model_name]

    async def acquire(self, model_name: str) -> None:
        """Wartet, bis ein Request für das gegebene Modell erlaubt ist."""
        await self.get_limiter(model_name).acquire()

    def get_wait_estimate(self, model_name: str) -> float:
        return self.get_limiter(model_name).get_wait_estimate()