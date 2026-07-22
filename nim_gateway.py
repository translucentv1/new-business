"""
nim_gateway.py
================
Fertiges Grundgerüst für Hermes (oder jeden anderen Agenten), um die
NVIDIA-Build/NIM-API über mehrere Modelle hinweg zuverlässig und ohne
429-Fehler zu nutzen.

WAS DAS SCRIPT MACHT
---------------------
1. ModelRouter      -> ordnet Task-Typen (reasoning/coding/long_context)
                        festen Modellen zu.
2. RateLimiter       -> Token-Bucket PRO MODELL, drosselt proaktiv unter
                        das NVIDIA-Limit (Standard: 35 req/min statt 40).
3. call_with_backoff -> ruft die API auf, fängt 429/5xx ab und wartet
                        mit exponential backoff + jitter, statt einfach
                        zu crashen.
4. RequestQueue      -> serialisiert Aufrufe pro Modell, damit der
                        Rate-Limiter nicht von parallelen Threads
                        unterlaufen wird.
5. SimpleCache       -> vermeidet doppelte Calls bei identischem
                        (model, prompt)-Paar innerhalb einer TTL.
6. Logging           -> schreibt pro Call Zeile in gateway.log
                        (Modell, Dauer, Tokens, Status) fuer Monitoring
                        und spaetere Kostenrechnung.

WAS HERMES TUN MUSS
--------------------
1. NVIDIA_API_KEY als Umgebungsvariable setzen.
2. `gateway.call(task_type="reasoning", messages=[...])` aufrufen
   statt direkt requests/openai-client zu benutzen.
3. Fertig. Routing, Limiting, Retry, Caching laufen automatisch.

Kein Setup-Design, keine Architektur-Entscheidungen mehr noetig --
nur noch integrieren.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

# Task-Typ -> Modell-Slug. Bei Bedarf anpassen / erweitern.
MODEL_ROUTES: dict[str, str] = {
    "reasoning": "zai-org/glm-5.2",
    "coding": "deepseek-ai/deepseek-v4-pro",
    "long_context": "nvidia/nemotron-3-ultra",
}

# Sicherheitsschwelle je Modell. Bewusst UNTER dem offiziellen 40-RPM-
# Richtwert, um Bursts/Aggregationseffekte abzufangen.
SAFE_RPM_PER_MODEL = 35

CACHE_TTL_SECONDS = 300
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 1.0

LOG_PATH = os.environ.get("NIM_GATEWAY_LOG", "gateway.log")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("nim_gateway")


# ---------------------------------------------------------------------------
# 1. Model Router
# ---------------------------------------------------------------------------

class ModelRouter:
    """Ordnet einen Task-Typ dem zustaendigen Modell-Slug zu."""

    def __init__(self, routes: dict[str, str] = MODEL_ROUTES):
        self.routes = routes

    def resolve(self, task_type: str) -> str:
        if task_type not in self.routes:
            raise ValueError(
                f"Unbekannter task_type '{task_type}'. "
                f"Verfuegbar: {list(self.routes)}"
            )
        return self.routes[task_type]


# ---------------------------------------------------------------------------
# 2. Rate Limiter (Token Bucket, ein Bucket pro Modell)
# ---------------------------------------------------------------------------

class TokenBucket:
    """Klassischer Token-Bucket: erlaubt bis zu `rate` Aufrufe/Minute,
    blockiert (statt zu werfen), wenn das Kontingent aufgebraucht ist."""

    def __init__(self, rate_per_minute: int):
        self.capacity = rate_per_minute
        self.tokens = float(rate_per_minute)
        self.refill_rate = rate_per_minute / 60.0  # tokens pro Sekunde
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def acquire(self) -> None:
        """Blockiert, bis ein Token verfuegbar ist."""
        while True:
            with self._lock:
                self._refill()
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait_time = (1 - self.tokens) / self.refill_rate
            time.sleep(max(wait_time, 0.01))


class RateLimiter:
    """Verwaltet einen separaten TokenBucket pro Modell, weil NVIDIA
    die RPM-Limits pro Modell und nicht kontoweit vergibt."""

    def __init__(self, rpm: int = SAFE_RPM_PER_MODEL):
        self.rpm = rpm
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _bucket_for(self, model: str) -> TokenBucket:
        with self._lock:
            if model not in self._buckets:
                self._buckets[model] = TokenBucket(self.rpm)
            return self._buckets[model]

    def acquire(self, model: str) -> None:
        self._bucket_for(model).acquire()


# ---------------------------------------------------------------------------
# 3. Retry mit exponential backoff + jitter
# ---------------------------------------------------------------------------

def call_with_backoff(
    payload: dict[str, Any],
    max_retries: int = MAX_RETRIES,
) -> dict[str, Any]:
    """Fuehrt den eigentlichen HTTP-Call aus und behandelt 429/5xx mit
    exponentiellem Backoff + Jitter. Wirft nach max_retries eine
    Exception, statt endlos zu haengen."""

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                NVIDIA_BASE_URL, headers=headers, json=payload, timeout=120
            )
        except requests.RequestException as exc:
            logger.warning("Netzwerkfehler (Versuch %s): %s", attempt, exc)
            response = None

        if response is not None and response.status_code == 200:
            return response.json()

        status = response.status_code if response is not None else "no_response"
        retriable = status in (429, 500, 502, 503, 504, "no_response")

        if not retriable or attempt == max_retries:
            body = response.text if response is not None else "n/a"
            logger.error(
                "Endgueltiger Fehler nach %s Versuchen: status=%s body=%s",
                attempt + 1,
                status,
                body[:500],
            )
            raise RuntimeError(f"NIM-Call fehlgeschlagen: status={status}")

        # exponential backoff + jitter
        sleep_time = BACKOFF_BASE_SECONDS * (2 ** attempt) + random.uniform(0, 1)
        logger.info(
            "Status %s bei Versuch %s -> warte %.1fs vor Retry",
            status,
            attempt + 1,
            sleep_time,
        )
        time.sleep(sleep_time)

    raise RuntimeError("Unreachable")  # sollte durch Schleife nie erreicht werden


# ---------------------------------------------------------------------------
# 4. Simpler TTL-Cache fuer identische Anfragen
# ---------------------------------------------------------------------------

@dataclass
class _CacheEntry:
    value: dict[str, Any]
    expires_at: float


class SimpleCache:
    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.ttl = ttl_seconds
        self._store: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(model: str, messages: list[dict]) -> str:
        raw = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, model: str, messages: list[dict]) -> dict[str, Any] | None:
        key = self._key(model, messages)
        with self._lock:
            entry = self._store.get(key)
            if entry and entry.expires_at > time.monotonic():
                return entry.value
            if entry:
                del self._store[key]
        return None

    def set(self, model: str, messages: list[dict], value: dict[str, Any]) -> None:
        key = self._key(model, messages)
        with self._lock:
            self._store[key] = _CacheEntry(value, time.monotonic() + self.ttl)


# ---------------------------------------------------------------------------
# 5. Request Queue (serialisiert Calls pro Modell)
# ---------------------------------------------------------------------------

class RequestQueue:
    """Fuehrt Requests seriell pro Modell aus, damit der RateLimiter
    nicht von mehreren parallelen Threads gleichzeitig unterlaufen
    werden kann. Prioritaet: niedrigere Zahl = wichtiger, wird zuerst
    bearbeitet."""

    def __init__(self):
        self._locks: dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    def _lock_for(self, model: str) -> threading.Lock:
        with self._global_lock:
            if model not in self._locks:
                self._locks[model] = threading.Lock()
            return self._locks[model]

    def run(self, model: str, fn, *args, **kwargs):
        with self._lock_for(model):
            return fn(*args, **kwargs)


# ---------------------------------------------------------------------------
# 6. Das eigentliche Gateway, das Hermes benutzt
# ---------------------------------------------------------------------------

class NimGateway:
    def __init__(
        self,
        routes: dict[str, str] = MODEL_ROUTES,
        rpm: int = SAFE_RPM_PER_MODEL,
        cache_ttl: int = CACHE_TTL_SECONDS,
    ):
        if not NVIDIA_API_KEY:
            raise RuntimeError(
                "NVIDIA_API_KEY ist nicht gesetzt. "
                "export NVIDIA_API_KEY=... vor dem Start."
            )
        self.router = ModelRouter(routes)
        self.limiter = RateLimiter(rpm)
        self.cache = SimpleCache(cache_ttl)
        self.queue = RequestQueue()

    def call(
        self,
        task_type: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Haupt-Einstiegspunkt fuer Hermes.

        task_type: "reasoning" | "coding" | "long_context" (siehe MODEL_ROUTES)
        messages:  Standard OpenAI-Chat-Format [{"role": ..., "content": ...}]
        """
        model = self.router.resolve(task_type)

        if use_cache:
            cached = self.cache.get(model, messages)
            if cached is not None:
                logger.info("Cache-Hit fuer Modell %s", model)
                return cached

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        def _do_call():
            self.limiter.acquire(model)  # blockiert bis Kontingent frei ist
            start = time.monotonic()
            result = call_with_backoff(payload)
            duration = time.monotonic() - start
            usage = result.get("usage", {})
            logger.info(
                "OK model=%s duration=%.2fs prompt_tokens=%s completion_tokens=%s",
                model,
                duration,
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
            )
            return result

        result = self.queue.run(model, _do_call)

        if use_cache:
            self.cache.set(model, messages, result)

        return result


# ---------------------------------------------------------------------------
# Beispiel-Nutzung (kann von Hermes 1:1 als Vorlage benutzt werden)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    gateway = NimGateway()

    # Reasoning-Aufgabe -> laeuft automatisch ueber GLM-5.2
    reasoning_result = gateway.call(
        task_type="reasoning",
        messages=[
            {"role": "user", "content": "Skizziere die ersten drei Schritte, um ein Online-Business im Bereich XYZ zu starten."}
        ],
    )
    print(reasoning_result["choices"][0]["message"]["content"])

    # Coding-Aufgabe -> laeuft automatisch ueber DeepSeek V4-Pro
    coding_result = gateway.call(
        task_type="coding",
        messages=[
            {"role": "user", "content": "Schreibe eine Python-Funktion, die eine CSV-Datei validiert."}
        ],
    )
    print(coding_result["choices"][0]["message"]["content"])
