"""Tolerant JSON-object parsing for LLM responses.

LLMs often wrap JSON in prose or code fences. This extracts a dict robustly so agents
don't crash on imperfect output — they degrade gracefully to a caller-supplied default.
"""
from __future__ import annotations

import json
import re


def parse_json_object(text: str, default: dict | None = None) -> dict:
    default = {} if default is None else default
    if not isinstance(text, str):
        return default

    candidate = text.strip()

    # Strip ```json ... ``` / ``` ... ``` fences.
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1).strip()

    try:
        data = json.loads(candidate)
        return data if isinstance(data, dict) else default
    except json.JSONDecodeError:
        pass

    # Last resort: grab the first {...} block embedded in surrounding text.
    block = re.search(r"\{.*\}", candidate, re.DOTALL)
    if block:
        try:
            data = json.loads(block.group(0))
            return data if isinstance(data, dict) else default
        except json.JSONDecodeError:
            pass
    return default
