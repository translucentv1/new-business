"""
Request-Queue mit Priorisierung.

Anfragen werden nicht parallel gefeuert, sondern über eine
Warteschlange seriell im erlaubten Tempo abgearbeitet.
Blockierende Schritte (Agent wartet) haben höhere Priorität
als Hintergrund-Tasks.

Priority-Level:
  0 = foreground (blocking)   — Agent wartet auf Ergebnis
  1 = background (non-block.) — Logging, Zusammenfassungen, Prefetch
"""

from __future__ import annotations

import asyncio
import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class PriorityLevel(enum.IntEnum):
    FOREGROUND = 0  # Blockierend — Agent wartet
    BACKGROUND = 1  # Nicht-blockierend — Logging, Prefetch
    BATCH = 2  # Gebatcht — wird gesammelt und gemeinsam verarbeitet


@dataclass(order=True)
class PrioritizedRequest:
    """
    Ein Request in der Warteschlange.

    Vergleichbar nach (priority, timestamp), damit asyncio.PriorityQueue
    funktioniert.
    """

    priority: int  # 0 = FOREGROUND, 1 = BACKGROUND
    timestamp: float = field(compare=True)
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    model_name: str = ""
    prompt: str = ""
    task: Callable = field(compare=False, default=lambda: None)
    future: asyncio.Future = field(compare=False, default=None)
    metadata: dict = field(default_factory=dict, compare=False)


class RequestQueue:
    """
    Priorisierte Async-Queue für NVIDIA-Requests.

    Ein Worker verarbeitet die Queue seriell (pro Modell),
    sodass Rate-Limits konsistent eingehalten werden.
    """

    def __init__(self, maxsize: int = 0):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=maxsize)
        self._pending_count: int = 0
        self._lock = asyncio.Lock()
        self._total_enqueued: int = 0
        self._total_dequeued: int = 0

    @property
    def pending(self) -> int:
        return self._queue.qsize()

    @property
    def total_enqueued(self) -> int:
        return self._total_enqueued

    @property
    def total_dequeued(self) -> int:
        return self._total_dequeued

    async def enqueue(
        self,
        model_name: str,
        prompt: str,
        task: Callable,
        priority: PriorityLevel = PriorityLevel.FOREGROUND,
        metadata: Optional[dict] = None,
    ) -> asyncio.Future:
        """
        Fügt einen Request in die Queue ein.

        Args:
            model_name: Ziel-Modell (für Monitoring)
            prompt: Prompt-Text (für Cache-Prüfung)
            task: Async-Callable, das den Request ausführt
            priority: FOREGROUND (0) oder BACKGROUND (1)
            metadata: Optionales Dict für Logging

        Returns:
            Future, die das Ergebnis des Tasks liefert.
        """
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        request = PrioritizedRequest(
            priority=int(priority),
            timestamp=time.monotonic(),
            model_name=model_name,
            prompt=prompt,
            task=task,
            future=future,
            metadata=metadata or {},
        )
        async with self._lock:
            await self._queue.put(request)
            self._total_enqueued += 1
        return future

    async def dequeue(self) -> PrioritizedRequest:
        """Nimmt den nächsten Request aus der Queue (blockiert wenn leer)."""
        request = await self._queue.get()
        self._total_dequeued += 1
        return request

    async def worker(self, executor: Callable, *args, **kwargs):
        """
        Endlos-Worker: holt Requests aus der Queue und führt sie aus.

        Args:
            executor: Async-Callable(request) → result
                      Wird für jeden dequeue-ten Request aufgerufen.
        """
        while True:
            request = await self.dequeue()
            try:
                result = await executor(request, *args, **kwargs)
                if request.future and not request.future.done():
                    request.future.set_result(result)
            except Exception as e:
                if request.future and not request.future.done():
                    request.future.set_exception(e)
            finally:
                self._queue.task_done()

    async def join(self):
        """Wartet, bis alle Requests in der Queue abgearbeitet sind."""
        await self._queue.join()