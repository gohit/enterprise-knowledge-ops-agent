"""Tests for the model-provider switch (Bedrock vs Azure config gating).

These exercise the configuration logic only — no client is instantiated, so no AWS or
Azure credentials are needed.
"""
from __future__ import annotations

from src import llm
from src.config import settings
from src.ingestion.index import embeddings_configured


def test_bedrock_chat_configured_with_region_and_model(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "bedrock")
    monkeypatch.setattr(settings, "aws_region", "us-east-1")
    monkeypatch.setattr(settings, "bedrock_chat_model_id", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    assert llm.chat_configured() is True


def test_bedrock_not_configured_when_missing(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "bedrock")
    monkeypatch.setattr(settings, "aws_region", "")
    monkeypatch.setattr(settings, "bedrock_chat_model_id", "")
    assert llm.chat_configured() is False


def test_bedrock_embeddings_configured(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "bedrock")
    monkeypatch.setattr(settings, "aws_region", "us-east-1")
    monkeypatch.setattr(settings, "bedrock_embed_model_id", "amazon.titan-embed-text-v2:0")
    assert embeddings_configured() is True


def test_azure_provider_uses_azure_fields(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "azure")
    monkeypatch.setattr(settings, "azure_openai_endpoint", "https://x.openai.azure.com/")
    monkeypatch.setattr(settings, "azure_openai_api_key", "key")
    monkeypatch.setattr(settings, "azure_openai_chat_deployment", "gpt-4o")
    assert llm.chat_configured() is True

    # AWS region present but provider is azure with no azure creds -> not configured.
    monkeypatch.setattr(settings, "azure_openai_api_key", "")
    assert llm.chat_configured() is False


def test_get_chat_llm_raises_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "bedrock")
    monkeypatch.setattr(settings, "aws_region", "")
    monkeypatch.setattr(settings, "bedrock_chat_model_id", "")
    try:
        llm.get_chat_llm()
        raised = False
    except RuntimeError:
        raised = True
    assert raised
