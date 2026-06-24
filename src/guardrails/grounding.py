"""Grounding / confidence policy.

Turns a numeric grounding score into a pass/fail verdict against the configured
threshold, and appends a disclaimer to answers that could not be fully grounded.
"""
from __future__ import annotations

from src.config import settings

DISCLAIMER = (
    "\n\n[Note: This answer could not be fully grounded in the source documents and may be "
    "incomplete or imprecise. Please verify against the official policy.]"
)


def verdict_for(score: float) -> str:
    """'pass' if the grounding score meets the threshold, else 'fail'."""
    return "pass" if score >= settings.grounding_threshold else "fail"


def with_disclaimer(answer: str) -> str:
    return answer + DISCLAIMER
