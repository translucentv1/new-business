"""
NIM Client — Async OpenAI-kompatibler Client für build.nvidia.com.

Integriert Router, Rate-Limiter, Backoff, Queue, Cache & Monitor
in einer kohärenten API.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import aiohttp

from .router import TaskType, ModelEndpoint, ModelRouter
from .rate_limiter import MultiModelRateLimiter
from .backoff import ExponentialBackoff
from .request_queue import PriorityLevel, RequestQueue
from .cache import ResponseCache, BatchDetector
from .monitor import Monitor


@dataclass
class NIMConfig:
    """Globale Konfiguration für den NIM-Client."""

    api_key: str = ""
    """NVIDIA API-Key. Leer = aus Umgebungsvariable NVIDIA_API_KEY"""

    base_url: str = "https://integrate.api.nvidia.com/v1/"
    """API-Base-URL (mit trailing slash für aiohttp)"""

    default_max_tokens: int = 4096
    """Standard-Max-Tokens pro Request"""

    temperature: float = 0.7
    """Default-Temperatur"""

    cache_ttl: float = 300.0
    """Cache-TTL in Sekunden"""

    batch_window: float = 2.0
    """Batch-Erkennungsfenster in Sekunden"""

    log_dir: str = ""
    """Log-Verzeichnis (leer = kein File-Logging)"""

    
class RateLimitError(Exception):
    """429 Too Many Requests (trotz Rate-Limiting)."""
    def __init__(self, model: str, retry_after: Optional[float] = None):
        self.model = model
        self.retry_after = retry_after
        self.status = 429
        super().__init__(f"Rate limit exceeded for {model}")


class NIMError(Exception):
    """Allgemeiner NVIDIA-API-Fehler."""
    def __init__(self, status: int, body: str, model: str):
        self.status = status
        self.body = body
        self.model = model
        super().__init__(f"NVIDIA API error {status} for {model}: {body[:200]}")


class TimeoutError_(Exception):
    """API-Timeout."""
    def __init__(self, model: str, timeout: float):
        self.model = model
        self.status = 504
        super().__init__(f"Timeout ({timeout}s) for {model}")


class NIMClient:
    """
    Async NIM-Client mit integriertem Rate-Limiting, Queuing & Caching.

    Usage:
        client = NIMClient(api_key="nvapi-...")
        result = await client.chat(
            prompt="Erkläre mir...",
            task_type=TaskType.REASONING  # oder auto-klassifizieren
        )
    """

    def __init__(
        self,
        api_key: str = "",
        config: Optional[NIMConfig] = None,
        router: Optional[ModelRouter] = None,
    ):
        self._config = config or NIMConfig()
        self._api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")

        if not self._api_key:
            raise ValueError(
                "NVIDIA API-Key fehlt. Setze NVIDIA_API_KEY oder übergib api_key."
            )

        # Subsysteme
        self.router = router or ModelRouter()
        self.rate_limiter = MultiModelRateLimiter(self.router.endpoints)
        self.queue = RequestQueue()
        self.cache = ResponseCache(default_ttl=self._config.cache_ttl)
        self.batch = BatchDetector(window=self._config.batch_window)
        self.backoff = ExponentialBackoff()
        self.monitor = Monitor(log_dir=self._config.log_dir)

        # HTTP-Session (wird beim ersten Call lazy erzeugt)
        self._session: Optional[aiohttp.ClientSession] = None

        # Worker-Task (wird mit start() gestartet)
        self._worker_task: Optional[asyncio.Task] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=120, connect=30)
            self._session = aiohttp.ClientSession(
                base_url=self._config.base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=timeout,
            )
        return self._session

    async def start(self) -> None:
        """Startet den Queue-Worker im Hintergrund."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(
                self.queue.worker(self._execute_request)
            )

    async def stop(self) -> None:
        """Räumt auf: schließt Session, stoppt Worker."""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()

    # ── Haupt-API ──────────────────────────────────────────────────────────

    async def chat(
        self,
        prompt: str,
        system_prompt: str = "",
        task_type: Optional[TaskType] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        priority: PriorityLevel = PriorityLevel.FOREGROUND,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Sendet einen Chat-Request an das passende NVIDIA-Modell.

        Automatisch:
        - Task-Klassifikation → Routing
        - Cache-Prüfung (bei Hit: sofortige Rückgabe)
        - Prioritär in die Queue eingereiht
        - Rate-Limiting + Backoff + Logging

        Args:
            prompt: Der User-Prompt.
            system_prompt: Optionaler System-Prompt.
            task_type: Erzwungener TaskType (None = automatisch).
            max_tokens: Maximale Antwort-Tokens.
            temperature: Kreativität (0.0 - 2.0).
            priority: FOREGROUND (blockierend) oder BACKGROUND.
            metadata: Metadaten fürs Logging.

        Returns:
            API-Antwort als Dict (OpenAI-kompatibel).
        """
        metadata = metadata or {}
        max_tokens = max_tokens or self._config.default_max_tokens
        temperature = temperature if temperature is not None else self._config.temperature

        # 1) Task-Klassifikation
        if task_type is None:
            task_type, endpoint = self.router.classify_and_resolve(prompt)
        else:
            endpoint = self.router.resolve(task_type)

        metadata["task_type"] = task_type.value
        metadata["model"] = endpoint.name

        # 2) Cache-Prüfung
        cache_key = self.cache.make_key(endpoint.name, prompt)
        if cached := self.cache.get(cache_key):
            self.monitor.record(
                model_name=endpoint.name,
                latency_ms=0,
                cache_hit=True,
            )
            return cached

        # 3) In Queue einreihen
        future = await self.queue.enqueue(
            model_name=endpoint.name,
            prompt=prompt,
            task=lambda: self._chat_internal(
                endpoint=endpoint,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            ),
            priority=priority,
            metadata={
                "cache_key": cache_key,
                "model": endpoint.name,
                **metadata,
            },
        )
        result = await future

        # 4) Ins Cache schreiben
        token_count = self._extract_token_count(result)
        self.cache.set(cache_key, result, model_name=endpoint.name, token_count=token_count)

        return result

    # ── Queue-Worker ───────────────────────────────────────────────────────

    async def _execute_request(self, request) -> Any:
        """
        Worker-Funktion: wird von der Queue für jeden Request aufgerufen.
        Enthält Rate-Limiting + API-Call + Logging.
        """
        from .request_queue import PrioritizedRequest as PReq
        req: PReq = request

        model_name = req.model_name
        metadata = req.metadata or {}

        # 1) Cache nochmal prüfen (könnte zwischenzeitlich von anderem Worker gesetzt sein)
        cache_key = metadata.get("cache_key", "")
        if cache_key and self.cache.get(cache_key):
            return self.cache.get(cache_key)

        # 2) Rate-Limiting
        await self.rate_limiter.acquire(model_name)

        # 3) API-Call mit Backoff
        t0 = time.monotonic()
        result: Optional[dict] = None
        error: Optional[str] = None
        status_code: Optional[int] = None
        tokens_in = 0
        tokens_out = 0

        try:
            result = await self.backoff.run(req.task)
            # Tokenschätzung aus Response
            tokens_in = self._extract_prompt_tokens(result)
            tokens_out = self._extract_completion_tokens(result)
            status_code = 200
        except RateLimitError as e:
            status_code = 429
            error = str(e)
        except NIMError as e:
            status_code = e.status
            error = str(e)
        except (asyncio.TimeoutError, TimeoutError_) as e:
            status_code = 504
            error = str(e)
        except Exception as e:
            status_code = 0
            error = f"{type(e).__name__}: {e}"

        # 4) Logging
        latency = (time.monotonic() - t0) * 1000
        self.monitor.record(
            model_name=model_name,
            latency_ms=latency,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            status_code=status_code,
            error=error,
        )

        if error:
            raise Exception(error)
        return result

    async def _chat_internal(
        self,
        endpoint: ModelEndpoint,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> dict:
        """Führt den eigentlichen API-Call aus."""
        session = await self._get_session()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": endpoint.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with session.post(
            "chat/completions",
            json=payload,
        ) as resp:
            body = await resp.text()

            if resp.status == 429:
                retry_after = resp.headers.get("Retry-After")
                raise RateLimitError(
                    model=endpoint.name,
                    retry_after=float(retry_after) if retry_after else None,
                )
            if resp.status >= 400:
                raise NIMError(status=resp.status, body=body, model=endpoint.name)

            return await resp.json()

    # ── Hilfsfunktionen ────────────────────────────────────────────────────

    @staticmethod
    def _extract_token_count(response: dict) -> int:
        """Extrahiert die Gesamt-Token-Zahl aus einer API-Response."""
        usage = response.get("usage", {})
        return usage.get("total_tokens", 0)

    @staticmethod
    def _extract_prompt_tokens(response: dict) -> int:
        usage = response.get("usage", {})
        return usage.get("prompt_tokens", 0)

    @staticmethod
    def _extract_completion_tokens(response: dict) -> int:
        usage = response.get("usage", {})
        return usage.get("completion_tokens", 0)

    def extract_content(self, response: dict) -> str:
        """Extrahiert den Text aus einer OpenAI-kompatiblen Response."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return str(response)

    # ── Convenience ────────────────────────────────────────────────────────

    async def chat_blocking(self, prompt: str, **kwargs) -> str:
        """
        Komfort-Methode: sendet Prompt + extrahiert Text.
        Blockiert, bis Ergebnis da ist.
        """
        result = await self.chat(
            prompt=prompt,
            priority=PriorityLevel.FOREGROUND,
            **kwargs,
        )
        return self.extract_content(result)

    async def chat_background(self, prompt: str, **kwargs) -> asyncio.Future:
        """
        Feuert einen Background-Request ab (Logging, Zusammenfassung).
        Gibt sofort ein Future zurück.
        """
        from .request_queue import PrioritizedRequest as PReq
        task_type = kwargs.pop("task_type", None)
        endpoint = self.router.resolve(task_type or TaskType.UNKNOWN)

        future = await self.queue.enqueue(
            model_name=endpoint.name,
            prompt=prompt,
            task=lambda: self._chat_internal(
                endpoint=endpoint, prompt=prompt, **kwargs
            ),
            priority=PriorityLevel.BACKGROUND,
            metadata={"task_type": "background"},
        )
        return future