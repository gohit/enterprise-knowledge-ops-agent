"""Chat LLM factory (provider-aware).

Isolates the chat-model provider behind one function so the rest of the system never
imports a model SDK directly. Supports AWS Bedrock (default) and Azure OpenAI, chosen
via ``settings.llm_provider``. Agents accept an injected client for offline tests; in
production they call ``get_chat_llm()``.
"""
from __future__ import annotations

from src.config import settings


def chat_configured() -> bool:
    """True when the active provider has the credentials/config it needs for chat."""
    return settings.chat_configured()


def get_chat_llm(temperature: float = 0.0):
    """Return a configured chat client for the active provider.

    Raises a clear error if not configured — offline callers should inject a fake LLM
    instead of calling this.
    """
    if not chat_configured():
        raise RuntimeError(
            f"Chat model is not configured for provider '{settings.llm_provider}'. "
            "Set the relevant values in .env (see .env.example)."
        )

    if settings.llm_provider == "bedrock":
        # Imported lazily so the package loads even without langchain-aws / boto3.
        from langchain_aws import ChatBedrockConverse

        from src.aws import get_bedrock_runtime_client

        return ChatBedrockConverse(
            model=settings.bedrock_chat_model_id,
            client=get_bedrock_runtime_client(),
            temperature=temperature,
        )

    from langchain_openai import AzureChatOpenAI

    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_chat_deployment,
        temperature=temperature,
    )
