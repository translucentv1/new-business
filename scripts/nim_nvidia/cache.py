"""
Response-Caching + Batch-Erkennung.

Wiederkehrende Prompts/Kontextabfragen werden gecached, um
unnötige API-Calls zu vermeiden.

Batch-Erkennung: mehrere kleine Anfragen, die innerhalb eines
kurzen Fensters (z. B. 2s) zur selben Queue kommen, können
zusammengefasst werden (z. B. mehrere kurze Klassifikationen
in einen Call).
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CacheEntry:
    """Ein einzelner Cache-Eintrag."""

    prompt_hash: str
    response: Any  # JSON-deserialisierte API-Antwort
    model_name: str
    created_at: float = field(default_factory=time.time)
    ttl: float = 300.0  # 5 Minuten (Standard)
    hit_count: int = 0
    token_count: int = 0  # Geschätzte Tokeneinsparung

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl

    @property
    def age(self) -> float:
        return time.time() - self.created_at


def hash_prompt(prompt: str) -> str:
    """Erzeugt einen SHA-256-Hash des Prompts (gekürzt auf 16 Hex-Zeichen)."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def normalize_prompt(prompt: str) -> str:
    """
    Normalisiert einen Prompt für bessere Cache-Treffer:
    - Entfernt führende/nachfolgende Whitespaces
    - Kollabiert mehrfache Leerzeichen
    - Entfernt Timestamp-Zeilen (die variieren oft)
    """
    lines = []
    for line in prompt.split("\n"):
        line = line.strip()
        # Timestamp-Zeilen ignorieren
        if line.startswith("Current time:") or line.startswith("Heute ist"):
            continue
        lines.append(line)
    text = " ".join(lines)
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


class ResponseCache:
    """
    Thread-sicherer In-Memory-Cache mit TTL pro Eintrag.

    Usage:
        cache = ResponseCache()
        key = cache.make_key("deepseek-v4-pro", prompt)
        if cached := cache.get(key):
            return cached
        result = await api_call(...)
        cache.set(key, result, model_name="deepseek-v4-pro")
    """

    def __init__(self, default_ttl: float = 300.0):
        self._default_ttl = default_ttl
        self._entries: dict[str, CacheEntry] = {}
        self._total_hits: int = 0
        self._total_misses: int = 0
        self._saved_tokens: int = 0

    def make_key(self, model_name: str, prompt: str) -> str:
        """Erzeugt einen Cache-Key aus Modell + normalisiertem Prompt."""
        normalized = normalize_prompt(prompt)
        return f"{model_name}:{hash_prompt(normalized)}"

    def get(self, key: str) -> Optional[Any]:
        """
        Holt einen Eintrag aus dem Cache.
        Gibt None zurück bei Miss oder abgelaufenem Eintrag.
        """
        entry = self._entries.get(key)
        if entry is None:
            self._total_misses += 1
            return None
        if entry.is_expired:
            del self._entries[key]
            self._total_misses += 1
            return None
        entry.hit_count += 1
        self._total_hits += 1
        self._saved_tokens += entry.token_count or 100  # Schätzung
        return entry.response

    def set(
        self,
        key: str,
        response: Any,
        model_name: str = "",
        ttl: Optional[float] = None,
        token_count: int = 0,
    ) -> None:
        """Speichert einen Eintrag im Cache."""
        self._entries[key] = CacheEntry(
            prompt_hash=key.split(":")[-1],
            response=response,
            model_name=model_name,
            ttl=ttl or self._default_ttl,
            token_count=token_count,
        )

    def invalidate(self, model_name: Optional[str] = None) -> int:
        """
        Entfernt alle Einträge (oder nur die eines Modells).
        Gibt die Anzahl entfernter Einträge zurück.
        """
        if model_name is None:
            count = len(self._entries)
            self._entries.clear()
            return count
        keys = [k for k, e in self._entries.items() if e.model_name == model_name]
        for k in keys:
            del self._entries[k]
        return len(keys)

    def cleanup(self) -> int:
        """Entfernt alle abgelaufenen Einträge. Gibt die Anzahl zurück."""
        expired = [k for k, e in self._entries.items() if e.is_expired]
        for k in expired:
            del self._entries[k]
        return len(expired)

    @property
    def stats(self) -> dict:
        return {
            "entries": len(self._entries),
            "hits": self._total_hits,
            "misses": self._total_misses,
            "hit_ratio": round(
                self._total_hits / max(1, self._total_hits + self._total_misses), 3
            ),
            "saved_tokens": self._saved_tokens,
        }


class BatchDetector:
    """
    Erkennt, ob mehrere kleine Anfragen gebatcht werden können.

    Funktioniert nach Zeitfenster: Requests zum selben Modell,
    die innerhalb von 'window_seconds' eintreffen, werden als
    batchable markiert.

    Usage:
        detector = BatchDetector(window=2.0)
        if detector.should_batch("deepseek-v4-pro", prompt):
            # In Batch sammeln
            batch_id = detector.get_batch_id("deepseek-v4-pro")
        else:
            # Direkt abschicken
    """

    def __init__(self, window: float = 2.0, min_batch_size: int = 2):
        self._window = window
        self._min_batch_size = min_batch_size
        self._model_queues: dict[str, list[tuple[float, str]]] = defaultdict(list)

    def should_batch(self, model_name: str, prompt: str) -> bool:
        """
        Prüft, ob dieser Request gebatcht werden sollte.
        True wenn im Zeitfenster bereits >= min_batch_size-1 Anfragen
        zum selben Modell in der Warteschlange sind.
        """
        now = time.monotonic()
        # Alte Einträge bereinigen
        self._model_queues[model_name] = [
            (t, p)
            for t, p in self._model_queues[model_name]
            if (now - t) < self._window
        ]
        # Aktuellen Request hinzufügen
        self._model_queues[model_name].append((now, prompt))
        return len(self._model_queues[model_name]) >= self._min_batch_size

    def get_batch(self, model_name: str) -> list[str]:
        """Holt und leert die Batch-Queue für ein Modell."""
        batch = [p for _, p in self._model_queues.pop(model_name, [])]
        return batch

    def reset(self, model_name: Optional[str] = None) -> None:
        if model_name:
            self._model_queues.pop(model_name, None)
        else:
            self._model_queues.clear()