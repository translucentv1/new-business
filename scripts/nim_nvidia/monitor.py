"""
Logging & Monitoring — pro Modell: RPM, 429-Rate, Latenz, Tokenverbrauch.

Schreibt strukturierte Logs in eine rotierende Datei und
hält einen aggregierten In-Memory-Status für Live-Abfragen.
Grundlage zur Nachjustierung der Limiter und zur Kostenberechnung.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Optional


@dataclass
class ModelStats:
    """Aggregierte Statistiken pro Modell."""

    model_name: str
    total_requests: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_latency_ms: float = 0.0
    rate_limit_hits: int = 0  # 429
    server_errors: int = 0  # 5xx
    timeouts: int = 0
    cache_hits: int = 0
    last_request_at: Optional[float] = None
    _window_timestamps: list[float] = field(default_factory=list)

    @property
    def avg_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def rpm(self) -> float:
        """Durchschnittliche Requests pro Minute in der letzten Stunde."""
        now = time.time()
        cutoff = now - 3600
        recent = [t for t in self._window_timestamps if t > cutoff]
        return len(recent) / 60.0 if recent else 0.0

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        errors = self.rate_limit_hits + self.server_errors + self.timeouts
        return errors / self.total_requests

    def record(
        self,
        latency_ms: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        status_code: Optional[int] = None,
        cache_hit: bool = False,
    ) -> None:
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self.total_tokens_input += tokens_in
        self.total_tokens_output += tokens_out
        self.last_request_at = time.time()
        self._window_timestamps.append(time.time())

        if cache_hit:
            self.cache_hits += 1

        if status_code == 429:
            self.rate_limit_hits += 1
        elif status_code and status_code >= 500:
            self.server_errors += 1

    def to_dict(self) -> dict:
        return {
            "model": self.model_name,
            "total_requests": self.total_requests,
            "rpm_avg": round(self.rpm, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "total_tokens_in": self.total_tokens_input,
            "total_tokens_out": self.total_tokens_output,
            "rate_limit_hits": self.rate_limit_hits,
            "server_errors": self.server_errors,
            "timeouts": self.timeouts,
            "cache_hits": self.cache_hits,
            "error_rate": round(self.error_rate, 4),
        }


class JsonFormatter(logging.Formatter):
    """Formatter, der Log-Einträge als JSON-Zeilen ausgibt."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        # Exception-Info anhängen
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


# NVIDIA-Modellpreise (USD pro 1M Tokens, Stand Juli 2026)
# (Schätzung basierend auf öffentlichen NVIDIA-NIM-Preisen)
_MODEL_PRICING: dict[str, dict[str, float]] = {
    "glm-5.2": {"input": 0.50, "output": 1.50},
    "deepseek-v4-pro": {"input": 0.75, "output": 2.00},
    "nemotron-3-ultra": {"input": 0.40, "output": 1.20},
}

_DEFAULT_PRICE = {"input": 0.50, "output": 1.50}


def estimate_cost(model_name: str, tokens_in: int, tokens_out: int) -> float:
    """Geschätzte Kosten in USD für einen Request."""
    pricing = _MODEL_PRICING.get(model_name, _DEFAULT_PRICE)
    cost_in = (tokens_in / 1_000_000) * pricing["input"]
    cost_out = (tokens_out / 1_000_000) * pricing["output"]
    return cost_in + cost_out


class Monitor:
    """
    Zentrales Monitoring fass alle Modelle.

    - Schreibt JSON-Zeilen-Logs in eine rotierende Datei.
    - Hält aggregierte Statistiken pro Modell im Speicher.
    - Bietet Live-Status-Abfragen.
    """

    def __init__(self, log_dir: str = "", log_level: int = logging.INFO):
        self._stats: dict[str, ModelStats] = defaultdict(
            lambda: ModelStats(model_name="unknown")
        )
        self._logger = logging.getLogger("nim_nvidia")
        self._logger.setLevel(log_level)
        self._logger.propagate = False

        # Rotierenden File-Handler einrichten
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, "nim_nvidia.log")
            handler = RotatingFileHandler(
                log_path, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB
            )
            handler.setFormatter(JsonFormatter())
            self._logger.addHandler(handler)

        # Console-Handler (optional, nur bei direktem Aufruf)
        if not log_dir:
            ch = logging.StreamHandler()
            ch.setFormatter(JsonFormatter())
            self._logger.addHandler(ch)

    def get_stats(self, model_name: str) -> ModelStats:
        """Liefert (oder erzeugt) die Statistik für ein Modell."""
        return self._stats[model_name]

    def record(
        self,
        model_name: str,
        latency_ms: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        status_code: Optional[int] = None,
        cache_hit: bool = False,
        error: Optional[str] = None,
    ) -> None:
        """Zeichnet einen abgeschlossenen API-Call auf."""
        stats = self._stats[model_name]
        stats.model_name = model_name
        stats.record(
            latency_ms=latency_ms,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            status_code=status_code,
            cache_hit=cache_hit,
        )

        # Kostenberechnung
        cost = estimate_cost(model_name, tokens_in, tokens_out)

        # JSON-Log-Eintrag
        extra = {
            "model": model_name,
            "latency_ms": round(latency_ms, 1),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "status": status_code,
            "cache_hit": cache_hit,
            "cost_usd": round(cost, 6),
        }
        if error:
            extra["error"] = error

        log_method = self._logger.warning if error else self._logger.info
        log_method(
            f"{'HIT' if cache_hit else 'MISS'} {model_name} "
            f"({latency_ms:.0f}ms, {tokens_in}+{tokens_out}t, ${cost:.6f})",
            extra=extra,
        )

    def all_stats(self) -> dict[str, dict]:
        """Liefert alle Statistiken als Dict."""
        return {
            name: stats.to_dict() for name, stats in self._stats.items()
        }

    def summary(self) -> dict:
        """Kompakter Gesamtüberblick."""
        total_reqs = sum(s.total_requests for s in self._stats.values())
        total_429 = sum(s.rate_limit_hits for s in self._stats.values())
        total_tokens_in = sum(s.total_tokens_input for s in self._stats.values())
        total_tokens_out = sum(s.total_tokens_output for s in self._stats.values())
        total_cost = estimate_cost("all", total_tokens_in, total_tokens_out)
        return {
            "total_requests": total_reqs,
            "total_429s": total_429,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "estimated_cost_usd": round(total_cost, 4),
            "models": self.all_stats(),
        }

    def get_model_summary_text(self) -> str:
        """Formatierte Text-Übersicht für Log/Report."""
        lines = ["── NVIDIA NIM Monitoring ──"]
        total_cost = 0.0
        for name, stats in sorted(self._stats.items()):
            s = stats.to_dict()
            cost = estimate_cost(
                name, stats.total_tokens_input, stats.total_tokens_output
            )
            total_cost += cost
            lines.append(
                f"{name:25s} | "
                f"Req:{s['total_requests']:4d}  RPM:{s['rpm_avg']:5.1f}  "
                f"Lat:{s['avg_latency_ms']:6.0f}ms  "
                f"429:{s['rate_limit_hits']:2d}  "
                f"Err:{s['server_errors']:1d}  "
                f"Cache:{s['cache_hits']:2d}  "
                f"${cost:.4f}"
            )
        lines.append(f"{'':->80s}")
        lines.append(f"{'GESAMT':25s} | ${total_cost:.4f}")
        return "\n".join(lines)