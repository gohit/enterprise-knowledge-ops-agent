r"""List the Bedrock models your account can actually use in the configured region.

Run after putting AWS credentials + region in .env:
    & ".\.venv\Scripts\python.exe" tools\list_bedrock_models.py

Shows ACTIVE Anthropic chat models and Amazon/Cohere embedding models, with how each
must be invoked (ON_DEMAND vs INFERENCE_PROFILE), plus available inference profiles.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.aws import get_bedrock_client  # noqa: E402
from src.config import settings  # noqa: E402

print(f"Region: {settings.aws_region}\n")
client = get_bedrock_client()


def show(title: str, *, provider: str, modality: str) -> None:
    print(f"=== {title} ===")
    try:
        models = client.list_foundation_models(
            byProvider=provider, byOutputModality=modality
        )["modelSummaries"]
    except Exception as exc:  # noqa: BLE001
        print("  (failed to list:", type(exc).__name__, str(exc)[:200], ")\n")
        return

    for m in models:
        status = (m.get("modelLifecycle") or {}).get("status", "?")
        if status != "ACTIVE":
            continue
        types = ",".join(m.get("inferenceTypesSupported", [])) or "—"
        print(f"  {m['modelId']:<55} [{types}]")
    print()


show("Anthropic chat models (ACTIVE)", provider="Anthropic", modality="TEXT")
show("Amazon embedding models (ACTIVE)", provider="Amazon", modality="EMBEDDING")
show("Cohere embedding models (ACTIVE)", provider="Cohere", modality="EMBEDDING")

print("=== Inference profiles (use these IDs for models marked INFERENCE_PROFILE) ===")
try:
    profiles = client.list_inference_profiles().get("inferenceProfileSummaries", [])
    for p in profiles:
        if "anthropic" in p.get("inferenceProfileId", "").lower() or "claude" in p.get("inferenceProfileName", "").lower():
            print(f"  {p['inferenceProfileId']:<55} ({p.get('status', '?')})")
except Exception as exc:  # noqa: BLE001
    print("  (failed to list inference profiles:", type(exc).__name__, str(exc)[:200], ")")
