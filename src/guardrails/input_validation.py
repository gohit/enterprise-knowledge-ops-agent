"""Input guardrail — the system's first line of defense.

Rejects empty/oversized input and detects common prompt-injection attempts before the
query reaches any agent or LLM. Pure logic, no LLM, fully unit-testable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from src.config import settings

# Patterns indicating an attempt to override system behavior or exfiltrate the prompt.
INJECTION_PATTERNS = [
    r"ignore\s+(all|any|the|your|previous|prior|above)?\s*(the\s+)?(previous|prior|above)?\s*instructions",
    r"disregard\s+(all|any|the|your|previous|prior|above).*instruction",
    r"forget\s+(all|everything|your|the).*(instruction|prompt)",
    r"system\s+prompt",
    r"reveal\s+(your|the)\s+(system\s+)?prompt",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(a\s+)?(dan|developer\s+mode)",
]


@dataclass
class InputCheck:
    valid: bool
    reason: str  # "ok" | "empty" | "too_long" | "injection"
    sanitized: str


def validate_input(query: str, max_chars: int | None = None) -> InputCheck:
    max_chars = max_chars or settings.max_query_chars
    text = (query or "").strip()

    if not text:
        return InputCheck(False, "empty", text)
    if len(text) > max_chars:
        return InputCheck(False, "too_long", text[:max_chars])
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return InputCheck(False, "injection", text)

    return InputCheck(True, "ok", text)
