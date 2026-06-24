r"""Verify model access end-to-end using the project's configured provider.

Run after filling .env:
    & ".\.venv\Scripts\python.exe" tools\check_model.py

Calls the chat model and the embedding model with a tiny request and reports the
result, so you can confirm credentials + model access before building the index.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings  # noqa: E402

print(f"Provider     : {settings.llm_provider}")
if settings.llm_provider == "bedrock":
    print(f"Region       : {settings.aws_region}")
    print(f"Chat model   : {settings.bedrock_chat_model_id}")
    print(f"Embed model  : {settings.bedrock_embed_model_id}")
print("-" * 50)

# --- chat ---
try:
    from src.llm import get_chat_llm

    resp = get_chat_llm().invoke("Reply with exactly one word: pong")
    print("CHAT  OK  ->", getattr(resp, "content", resp))
except Exception as exc:  # noqa: BLE001
    print("CHAT  FAILED ->", type(exc).__name__, str(exc)[:300])

# --- embeddings ---
try:
    from src.ingestion.index import get_embeddings

    vec = get_embeddings().embed_query("hello world")
    print(f"EMBED OK  -> vector dimension {len(vec)}")
except Exception as exc:  # noqa: BLE001
    print("EMBED FAILED ->", type(exc).__name__, str(exc)[:300])
