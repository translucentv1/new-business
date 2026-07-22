"""
resilient_gateway.py
======================
Erweiterte Version von nim_gateway.py: statt bei einem Fehler (429,
5xx, Timeout, Auth-Fehler, ...) den ganzen Prozess zu stoppen, wird
automatisch die naechste Provider/Modell-Kombination aus einer
Fallback-Kette versucht -- so lange, bis eine funktioniert oder alle
Optionen erschoepft sind. Fuer echten 24/7-Betrieb gibt es zusaetzlich
einen "resilient loop"-Wrapper, der selbst bei unerwarteten Exceptions
den Prozess am Laufen haelt statt abzustuerzen.

KONZEPT
-------
1. PROVIDERS       -> Zugangsdaten/Base-URLs fuer Nous Portal,
                       OpenRouter, NVIDIA NIM (beliebig erweiterbar).
2. FALLBACK_CHAINS  -> pro task_type eine geordnete Liste von
                       (provider, model_slug)-Paaren. Wird Eintrag 1
                       blockiert/fehlerhaft, folgt automatisch Eintrag 2, 3, ...
3. CircuitBreaker   -> merkt sich pro (provider, model), wann zuletzt
                       ein Fehler auftrat, und ueberspringt es fuer eine
                       Cooldown-Zeit, statt es bei jedem Call erneut zu
                       verzoegern.
4. call()           -> versucht die Kette der Reihe nach durch. Nur
                       wenn WIRKLICH ALLE Optionen fehlschlagen, wird
                       eine Exception geworfen -- der Aufrufer kann
                       diese fangen und z.B. die Aufgabe spaeter erneut
                       versuchen, statt dass der ganze Agent stirbt.
5. run_forever()    -> Beispiel-Loop, der selbst bei kompletten
                       Kettenausfaellen (z.B. Internet down) nicht
                       abstuerzt, sondern wartet und weitermacht.
                       Das ist der Baustein fuer echten 24/7-Betrieb.

WAS HERMES TUN MUSS
--------------------
1. API-Keys als Env-Variablen setzen (siehe PROVIDERS unten).
2. gateway.call(task_type=..., messages=[...]) aufrufen -- wie bisher.
3. Fuer Dauerbetrieb: die eigene Verarbeitungsschleife mit
   `safe_forever(...)` umwickeln (Beispiel ganz unten), statt eigene
   try/except-Bloecke zu bauen.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

import requests

# ---------------------------------------------------------------------------
# Provider-Konfiguration
# ---------------------------------------------------------------------------

@dataclass
class Provider:
    name: str
    base_url: str
    api_key_env: str
    extra_headers: dict[str, str] = field(default_factory=dict)

    def headers(self) -> dict[str, str]:
        key = os.environ.get(self.api_key_env, "")
        h = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        h.update(self.extra_headers)
        return h


PROVIDERS: dict[str, Provider] = {
    "nous_portal": Provider(
        name="nous_portal",
        base_url="https://portal.nousresearch.com/v1/chat/completions",
        api_key_env="NOUS_PORTAL_API_KEY",
    ),
    "openrouter": Provider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        api_key_env="OPENROUTER_API_KEY",
    ),
    "nvidia_nim": Provider(
        name="nvidia_nim",
        base_url="https://integrate.api.nvidia.com/v1/chat/completions",
        api_key_env="NVIDIA_API_KEY",
    ),
}

# Pro task_type eine geordnete Fallback-Kette: (provider_key, model_slug).
# Reihenfolge = Prioritaet. Bei Fehler/Cooldown wird automatisch der
# naechste Eintrag versucht. Slugs vor Produktivbetrieb gegen die
# jeweiligen Kataloge pruefen -- Namen aendern sich gelegentlich.
FALLBACK_CHAINS: dict[str, list[tuple[str, str]]] = {
    "reasoning": [
        ("nous_portal", "zai-org/glm-5.2"),
        ("openrouter", "tencent/hy3"),
        ("nvidia_nim", "zai-org/glm-5.2"),
        ("openrouter", "stepfun-ai/step-3.7-flash"),
    ],
    "coding": [
        ("nous_portal", "deepseek/deepseek-v4-pro"),
        ("openrouter", "poolside/laguna-s-2.1"),
        ("nvidia_nim", "deepseek-ai/deepseek-v4-pro"),
        ("openrouter", "poolside/laguna-xs-2.1"),
    ],
    "long_context": [
        ("nous_portal", "nvidia/nemotron-3-ultra"),
        ("openrouter", "nvidia/nemotron-3-ultra"),
        ("nvidia_nim", "nvidia/nemotron-3-ultra"),
    ],
}

SAFE_RPM_PER_MODEL = 35
CACHE_TTL_SECONDS = 300
MAX_RETRIES_PER_MODEL = 3          # Retries INNERHALB eines Modells
BACKOFF_BASE_SECONDS = 1.0
CIRCUIT_COOLDOWN_SECONDS = 60      # wie lange ein gefeuertes Modell pausiert
CHAIN_EXHAUSTED_WAIT_SECONDS = 30  # Pause, wenn ALLE Optionen gerade blockiert sind

LOG_PATH = os.environ.get("GATEWAY_LOG", "gateway.log")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("resilient_gateway")
# zusaetzlich auf Konsole ausgeben, damit man 24/7-Laeufe live sieht
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(console)


# ---------------------------------------------------------------------------
# Token Bucket Rate Limiter (pro provider+model)
# ---------------------------------------------------------------------------

class TokenBucket:
    def __init__(self, rate_per_minute: int):
        self.capacity = rate_per_minute
        self.tokens = float(rate_per_minute)
        self.refill_rate = rate_per_minute / 60.0
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def try_acquire(self) -> bool:
        """Non-blocking Variante: gibt False zurueck statt zu warten,
        damit der Aufrufer stattdessen sofort auf den naechsten
        Fallback in der Kette wechseln kann."""
        with self._lock:
            self._refill()
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def acquire_blocking(self) -> None:
        while not self.try_acquire():
            time.sleep(0.2)


class RateLimiterPool:
    def __init__(self, rpm: int = SAFE_RPM_PER_MODEL):
        self.rpm = rpm
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _key(self, provider: str, model: str) -> str:
        return f"{provider}:{model}"

    def _bucket_for(self, provider: str, model: str) -> TokenBucket:
        key = self._key(provider, model)
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(self.rpm)
            return self._buckets[key]

    def try_acquire(self, provider: str, model: str) -> bool:
        return self._bucket_for(provider, model).try_acquire()


# ---------------------------------------------------------------------------
# Circuit Breaker: haelt zuletzt fehlgeschlagene (provider, model)
# Kombinationen fuer eine Cooldown-Zeit fern, statt sie jedes Mal neu
# zu versuchen und dabei Zeit zu verlieren.
# ---------------------------------------------------------------------------

class CircuitBreaker:
    def __init__(self, cooldown_seconds: int = CIRCUIT_COOLDOWN_SECONDS):
        self.cooldown = cooldown_seconds
        self._tripped_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def _key(self, provider: str, model: str) -> str:
        return f"{provider}:{model}"

    def is_open(self, provider: str, model: str) -> bool:
        """True = Kreis offen = NICHT versuchen (noch im Cooldown)."""
        key = self._key(provider, model)
        with self._lock:
            until = self._tripped_until.get(key)
            return until is not None and time.monotonic() < until

    def trip(self, provider: str, model: str) -> None:
        key = self._key(provider, model)
        with self._lock:
            self._tripped_until[key] = time.monotonic() + self.cooldown
        logger.warning("Circuit OPEN fuer %s (Cooldown %ss)", key, self.cooldown)

    def reset(self, provider: str, model: str) -> None:
        key = self._key(provider, model)
        with self._lock:
            self._tripped_until.pop(key, None)


# ---------------------------------------------------------------------------
# Cache
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
    def _key(messages: list[dict], task_type: str) -> str:
        raw = json.dumps({"task_type": task_type, "messages": messages}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, task_type: str, messages: list[dict]) -> dict[str, Any] | None:
        key = self._key(messages, task_type)
        with self._lock:
            entry = self._store.get(key)
            if entry and entry.expires_at > time.monotonic():
                return entry.value
            if entry:
                del self._store[key]
        return None

    def set(self, task_type: str, messages: list[dict], value: dict[str, Any]) -> None:
        key = self._key(messages, task_type)
        with self._lock:
            self._store[key] = _CacheEntry(value, time.monotonic() + self.ttl)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class ModelUnavailable(Exception):
    """Ein einzelnes Modell ist gerade nicht nutzbar (429, 5xx, Timeout,
    Auth-Fehler). Wird intern gefangen, um zum naechsten Fallback zu
    wechseln -- sollte den Aufrufer normalerweise NICHT erreichen."""


class AllFallbacksExhausted(Exception):
    """ALLE Modelle in der Kette sind aktuell nicht nutzbar. Das ist
    der einzige Fehler, den `call()` nach aussen wirft -- und selbst
    der stoppt bei Verwendung von `safe_call()` den Gesamtprozess
    nicht, siehe unten."""


# ---------------------------------------------------------------------------
# Kern: ein Call gegen genau EIN (provider, model) -- mit Retries
# ---------------------------------------------------------------------------

def _single_model_call(
    provider: Provider,
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    max_retries: int = MAX_RETRIES_PER_MODEL,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                provider.base_url,
                headers=provider.headers(),
                json=payload,
                timeout=120,
            )
        except requests.RequestException as exc:
            logger.warning(
                "[%s/%s] Netzwerkfehler (Versuch %s): %s",
                provider.name, model, attempt + 1, exc,
            )
            if attempt == max_retries:
                raise ModelUnavailable(f"network error: {exc}") from exc
            time.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt) + random.uniform(0, 1))
            continue

        if response.status_code == 200:
            return response.json()

        status = response.status_code
        retriable = status in (429, 500, 502, 503, 504)

        if not retriable:
            # z.B. 400 (bad request), 401/403 (auth) -> sofort als
            # "Modell nicht nutzbar" werten, kein sinnloses Retry.
            logger.error(
                "[%s/%s] Nicht-retriable Fehler status=%s body=%s",
                provider.name, model, status, response.text[:300],
            )
            raise ModelUnavailable(f"status={status}")

        if attempt == max_retries:
            logger.warning(
                "[%s/%s] Retries erschoepft, letzter status=%s",
                provider.name, model, status,
            )
            raise ModelUnavailable(f"status={status} after {max_retries} retries")

        sleep_time = BACKOFF_BASE_SECONDS * (2 ** attempt) + random.uniform(0, 1)
        logger.info(
            "[%s/%s] status=%s -> Retry in %.1fs (Versuch %s/%s)",
            provider.name, model, status, sleep_time, attempt + 1, max_retries,
        )
        time.sleep(sleep_time)

    raise ModelUnavailable("unreachable")  # defensive


# ---------------------------------------------------------------------------
# Das Gateway: klappert die Fallback-Kette ab
# ---------------------------------------------------------------------------

class ResilientGateway:
    def __init__(
        self,
        chains: dict[str, list[tuple[str, str]]] = FALLBACK_CHAINS,
        providers: dict[str, Provider] = PROVIDERS,
        rpm: int = SAFE_RPM_PER_MODEL,
        cache_ttl: int = CACHE_TTL_SECONDS,
        circuit_cooldown: int = CIRCUIT_COOLDOWN_SECONDS,
    ):
        self.chains = chains
        self.providers = providers
        self.limiter = RateLimiterPool(rpm)
        self.cache = SimpleCache(cache_ttl)
        self.breaker = CircuitBreaker(circuit_cooldown)

    def call(
        self,
        task_type: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Versucht die Fallback-Kette fuer `task_type` der Reihe nach.
        Wirft NUR dann AllFallbacksExhausted, wenn WIRKLICH JEDE Option
        in der Kette gerade nicht funktioniert."""

        if task_type not in self.chains:
            raise ValueError(
                f"Unbekannter task_type '{task_type}'. Verfuegbar: {list(self.chains)}"
            )

        if use_cache:
            cached = self.cache.get(task_type, messages)
            if cached is not None:
                logger.info("Cache-Hit fuer task_type=%s", task_type)
                return cached

        chain = self.chains[task_type]
        last_error: Exception | None = None

        for provider_key, model in chain:
            provider = self.providers.get(provider_key)
            if provider is None:
                logger.error("Unbekannter Provider '%s' in Kette, ueberspringe", provider_key)
                continue

            if not os.environ.get(provider.api_key_env):
                logger.warning(
                    "[%s] Kein API-Key (%s) gesetzt, ueberspringe %s",
                    provider.name, provider.api_key_env, model,
                )
                continue

            if self.breaker.is_open(provider_key, model):
                logger.info("[%s/%s] Circuit offen (Cooldown), ueberspringe", provider_key, model)
                continue

            if not self.limiter.try_acquire(provider_key, model):
                logger.info(
                    "[%s/%s] Rate-Limit lokal ausgeschoepft, ueberspringe auf naechsten Fallback",
                    provider_key, model,
                )
                continue

            try:
                start = time.monotonic()
                result = _single_model_call(
                    provider, model, messages, temperature, max_tokens
                )
                duration = time.monotonic() - start
                usage = result.get("usage", {})
                logger.info(
                    "OK [%s/%s] duration=%.2fs prompt_tokens=%s completion_tokens=%s",
                    provider_key, model, duration,
                    usage.get("prompt_tokens"), usage.get("completion_tokens"),
                )
                self.breaker.reset(provider_key, model)

                if use_cache:
                    self.cache.set(task_type, messages, result)
                return result

            except ModelUnavailable as exc:
                logger.warning("[%s/%s] nicht nutzbar: %s -> naechster Fallback", provider_key, model, exc)
                self.breaker.trip(provider_key, model)
                last_error = exc
                continue

        # komplette Kette durch, nichts hat funktioniert
        raise AllFallbacksExhausted(
            f"Alle Fallbacks fuer task_type='{task_type}' fehlgeschlagen. "
            f"Letzter Fehler: {last_error}"
        )

    def call_safe(
        self,
        task_type: str,
        messages: list[dict[str, str]],
        **kwargs,
    ) -> dict[str, Any] | None:
        """Wie call(), aber wirft NIE eine Exception nach aussen.
        Gibt bei komplettem Kettenausfall None zurueck und loggt den
        Vorfall -- der Aufrufer kann dann selbst entscheiden (z.B.
        Aufgabe in eine Retry-Queue legen), OHNE dass der Prozess
        stirbt."""
        try:
            return self.call(task_type, messages, **kwargs)
        except AllFallbacksExhausted as exc:
            logger.error("call_safe: %s", exc)
            return None
        except Exception:
            # Absoluter Sicherheitsnetz-Fang: irgendein unerwarteter Bug
            # im Gateway selbst soll den Agenten trotzdem nicht toeten.
            logger.error("call_safe: unerwarteter Fehler:\n%s", traceback.format_exc())
            return None


# ---------------------------------------------------------------------------
# 24/7-Betrieb: resilient loop, der auch bei Totalausfall weiterlaeuft
# ---------------------------------------------------------------------------

def run_forever(
    work_fn: Callable[[], None],
    idle_sleep_seconds: float = 5.0,
) -> None:
    """Fuehrt work_fn() in einer Endlosschleife aus. Jede Exception --
    auch komplett unerwartete, auch AllFallbacksExhausted, auch Bugs in
    work_fn selbst -- wird geloggt, danach wird kurz gewartet und die
    Schleife laeuft weiter. Der Prozess stirbt nur noch durch bewusstes
    Beenden (Ctrl+C / SIGTERM / Prozessmanager-Stop), nie durch einen
    einzelnen fehlgeschlagenen Task-Schritt.

    Nutzung:
        gateway = ResilientGateway()

        def one_step():
            result = gateway.call_safe(task_type="reasoning", messages=[...])
            if result is None:
                logger.info("Kein Modell verfuegbar gerade, versuche es spaeter erneut")
                return
            # ... Ergebnis verarbeiten ...

        run_forever(one_step)
    """
    logger.info("=== resilient loop gestartet (PID %s) ===", os.getpid())
    consecutive_failures = 0

    while True:
        try:
            work_fn()
            consecutive_failures = 0
        except KeyboardInterrupt:
            logger.info("Manuell gestoppt (KeyboardInterrupt). Beende sauber.")
            break
        except Exception:
            consecutive_failures += 1
            logger.error(
                "Unerwarteter Fehler in work_fn (in Folge: %s):\n%s",
                consecutive_failures, traceback.format_exc(),
            )
            # bei wiederholten Totalausfaellen (z.B. Internet down)
            # Wartezeit progressiv erhoehen, um nicht sinnlos zu spinnen
            backoff = min(idle_sleep_seconds * (2 ** min(consecutive_failures, 6)), 300)
            logger.info("Warte %.0fs vor naechstem Versuch", backoff)
            time.sleep(backoff)
            continue

        time.sleep(idle_sleep_seconds)


# ---------------------------------------------------------------------------
# Beispiel-Nutzung
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    gateway = ResilientGateway()

    def one_step():
        result = gateway.call_safe(
            task_type="reasoning",
            messages=[{"role": "user", "content": "Testaufruf fuer den resilient loop."}],
        )
        if result is None:
            logger.info("Aktuell kein Modell verfuegbar -- wird im naechsten Zyklus erneut versucht.")
            return
        content = result["choices"][0]["message"]["content"]
        logger.info("Antwort erhalten: %s", content[:200])

    run_forever(one_step, idle_sleep_seconds=5.0)
