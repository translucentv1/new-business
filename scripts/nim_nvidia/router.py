"""
Model Router — ordnet Task-Typen konsistent NVIDIA-Modellen zu.

TaskType -> ModelEndpoint
  REASONING     -> GLM-5.2
  CODING        -> DeepSeek V4-Pro
  LONG_CONTEXT  -> Nemotron 3 Ultra

Jedes Modell hat sein eigenes Rate-Limit (>assert< wird nicht gemixt).
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field
from typing import Optional


class TaskType(enum.Enum):
    """Aufgabentyp, der das Ziel-Modell bestimmt."""

    REASONING = "reasoning"
    """Planung, Architektur, Analyse, Reflexion — GLM-5.2"""

    CODING = "coding"
    """Code-Generierung, Task-Execution, Debugging — DeepSeek V4-Pro"""

    LONG_CONTEXT = "long_context"
    """Dokumentenverarbeitung, lange Prompts (>8K Tokens) — Nemotron 3 Ultra"""

    UNKNOWN = "unknown"
    """Fallback; wird dem Default-Modell zugewiesen."""


@dataclass(frozen=True)
class ModelEndpoint:
    """Konfiguration eines NVIDIA-NIM-Modell-Endpunkts."""

    name: str
    """Modell-Name (z. B. 'glm-5.2', 'deepseek-v4-pro')"""

    model_id: str
    """NVIDIA-Modell-ID für den API-Call (z. B. 'nvidia/glm-5.2')"""

    rpm_limit: int = 35
    """Proaktives Rate-Limit in Requests/Minute (unter dem 40er-NVIDIA-Limit)"""

    max_tokens: int = 8192
    """Maximale Ausgabetokens für dieses Modell"""

    context_window: int = 131072
    """Maximaler Eingabe-Kontext (Tokens)"""

    endpoint_url: str = ""
    """Optional: abweichender API-Endpunkt. Leer = Standard."""

    task_types: set[TaskType] = field(default_factory=lambda: {TaskType.UNKNOWN})
    """Welche TaskTypes dieses Modell bedient."""


# ── Default-Konfiguration ──────────────────────────────────────────────────

DEFAULT_ENDPOINTS: list[ModelEndpoint] = [
    ModelEndpoint(
        name="glm-5.2",
        model_id="nvidia/glm-5.2",
        rpm_limit=35,
        max_tokens=16384,
        context_window=131072,
        task_types={TaskType.REASONING},
    ),
    ModelEndpoint(
        name="deepseek-v4-pro",
        model_id="nvidia/deepseek-v4-pro",
        rpm_limit=35,
        max_tokens=16384,
        context_window=131072,
        task_types={TaskType.CODING},
    ),
    ModelEndpoint(
        name="nemotron-3-ultra",
        model_id="nvidia/nemotron-3-ultra",
        rpm_limit=35,
        max_tokens=16384,
        context_window=524288,  # 512K — für Dokumente
        task_types={TaskType.LONG_CONTEXT},
    ),
]

# ── Heuristische Task-Erkennung ────────────────────────────────────────────

# Keywords, die auf den Aufgabentyp hinweisen
_REASONING_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.I)
    for p in [
        r"\b(plan|architektur|design|entwurf|strategie)\w*",
        r"\b(überleg|abwäg|reflektier|analysier|bewert)\w*",
        r"\b(reason|think|why|trade.?off)\w*",
        r"\bsollte\s+(ich|man|das|es)\b",
        r"\bvor.? und nachteile?\b",
    ]
]

_CODING_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.I)
    for p in [
        r"\b(code|implementier|programmier|schreib\s+funktion)\w*",
        r"\b(refactor|debug|fix|bug|test|unittest)\w*",
        r"\b(python|javascript|typescript|rust|java|go|bash)\b",
        r"\b(api|endpoint|route|middleware|schema)\w*",
        r"\b(git|commit|pr|merge|branch)\b",
    ]
]

_LONG_CONTEXT_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.I)
    for p in [
        r"\b(dokument|verarbeit|analysier\s+datei|lies\s+die\s+datei)\w*",
        r"\b(zusammenfass|extrakt|fasse\s+zusam)\w*",
        r"\b(seite|buch|kapitel|abschnitt)\w+",
        r"\b(kontext\s+länger\s+als|mehr\s+als\s+\d+k)\b",
    ]
]


def classify_task(prompt: str, token_count: int = 0) -> TaskType:
    """Bestimmt den TaskType aus Prompt + optionaler Token-Zahl."""
    # Lange Prompts → LONG_CONTEXT
    if token_count > 8_000:
        return TaskType.LONG_CONTEXT

    # Klassifikation über Keywords
    if any(p.search(prompt) for p in _CODING_PATTERNS):
        return TaskType.CODING
    if any(p.search(prompt) for p in _LONG_CONTEXT_PATTERNS):
        return TaskType.LONG_CONTEXT
    if any(p.search(prompt) for p in _REASONING_PATTERNS):
        return TaskType.REASONING

    # Minimale Heuristik: Code-Blöcke erkennen
    if "```" in prompt or "def " in prompt or "class " in prompt:
        return TaskType.CODING

    return TaskType.UNKNOWN


class ModelRouter:
    """Ordnet TaskType → ModelEndpoint zu."""

    def __init__(self, endpoints: Optional[list[ModelEndpoint]] = None):
        self._endpoints: list[ModelEndpoint] = endpoints or DEFAULT_ENDPOINTS
        # Lookup von TaskType → Endpoint
        self._task_map: dict[TaskType, ModelEndpoint] = {}
        for ep in self._endpoints:
            for tt in ep.task_types:
                self._task_map[tt] = ep

    @property
    def endpoints(self) -> list[ModelEndpoint]:
        return list(self._endpoints)

    def resolve(self, task_type: TaskType) -> ModelEndpoint:
        """Liefert den Endpoint für einen TaskType."""
        if task_type in self._task_map:
            return self._task_map[task_type]
        # Fallback: erstes Endpoint mit UNKNOWN oder einfach erstes
        fallback = self._task_map.get(TaskType.UNKNOWN, self._endpoints[0])
        return fallback

    def classify_and_resolve(
        self, prompt: str, token_count: int = 0
    ) -> tuple[TaskType, ModelEndpoint]:
        """Klassifiziert den Prompt und liefert TaskType + Endpoint."""
        task_type = classify_task(prompt, token_count)
        endpoint = self.resolve(task_type)
        return task_type, endpoint

    def get_endpoint(self, name: str) -> Optional[ModelEndpoint]:
        """Findet einen Endpoint per Name."""
        for ep in self._endpoints:
            if ep.name == name:
                return ep
        return None