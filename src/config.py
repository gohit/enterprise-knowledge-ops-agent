"""Central configuration for the Enterprise Knowledge Ops Agent.

All tunables (paths, model deployments, chunking, retrieval, guardrail thresholds)
live here and are loaded from environment / a local .env file via pydantic-settings.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = parent of the src/ package.
ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Model provider switch: "bedrock" or "azure" ---
    llm_provider: str = "bedrock"

    # --- Azure OpenAI ---
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_chat_deployment: str = ""
    azure_openai_embed_deployment: str = ""

    # --- AWS Bedrock ---
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""       # optional: leave blank to use the default
    aws_secret_access_key: str = ""   # boto3 credential chain (SSO / role / env)
    aws_session_token: str = ""
    bedrock_chat_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0"

    # --- Paths ---
    source_docs_dir: Path = ROOT / "Policies"
    vectorstore_dir: Path = ROOT / "data" / "vectorstore"
    logs_dir: Path = ROOT / "logs"

    # --- Vector store ---
    collection_name: str = "enterprise_policies"

    # --- Chunking ---
    chunk_size: int = 800
    chunk_overlap: int = 120

    # --- Retrieval ---
    top_k: int = 4
    min_relevance: float = 0.2  # below this, retrieval is treated as insufficient

    # --- Guardrails / grounding ---
    grounding_threshold: float = 0.75  # min grounding score to accept an answer
    max_retries: int = 2  # bounded re-plan/re-retrieve attempts
    max_query_chars: int = 2000

    def azure_configured(self) -> bool:
        """True when the minimum Azure OpenAI settings are present."""
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_embed_deployment
        )

    def chat_configured(self) -> bool:
        """True when the active provider has what it needs for the chat model."""
        if self.llm_provider == "bedrock":
            return bool(self.aws_region and self.bedrock_chat_model_id)
        return bool(
            self.azure_openai_endpoint
            and self.azure_openai_api_key
            and self.azure_openai_chat_deployment
        )

    def embeddings_configured(self) -> bool:
        """True when the active provider has what it needs for embeddings."""
        if self.llm_provider == "bedrock":
            return bool(self.aws_region and self.bedrock_embed_model_id)
        return self.azure_configured()


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
