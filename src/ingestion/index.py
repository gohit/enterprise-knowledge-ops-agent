r"""Embed document chunks and persist them in a Chroma vector store.

Run as a module to (re)build the index:
    .\.venv\Scripts\python.exe -m src.ingestion.index --rebuild

Requires Azure OpenAI credentials in .env (embedding deployment).
"""
from __future__ import annotations

import argparse
import shutil

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import settings
from src.ingestion.loader import load_and_split


def embeddings_configured() -> bool:
    return settings.embeddings_configured()


def get_embeddings():
    """Embedding client for the active provider (Bedrock default, or Azure)."""
    if not embeddings_configured():
        raise RuntimeError(
            f"Embeddings are not configured for provider '{settings.llm_provider}'. "
            "Set the relevant values in .env (see .env.example)."
        )

    if settings.llm_provider == "bedrock":
        from langchain_aws import BedrockEmbeddings

        from src.aws import get_bedrock_runtime_client

        return BedrockEmbeddings(
            model_id=settings.bedrock_embed_model_id,
            client=get_bedrock_runtime_client(),
        )

    from langchain_openai import AzureOpenAIEmbeddings

    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_embed_deployment,
    )


def get_vectorstore() -> Chroma:
    """Open (or create) the persistent Chroma collection."""
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.vectorstore_dir),
    )


def build_index(rebuild: bool = False) -> int:
    """Load + chunk the source PDFs and write them to the vector store.

    Returns the number of chunks indexed.
    """
    if rebuild and settings.vectorstore_dir.exists():
        shutil.rmtree(settings.vectorstore_dir)
    settings.vectorstore_dir.mkdir(parents=True, exist_ok=True)

    chunks: list[Document] = load_and_split()
    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    return len(chunks)


def retrieve(query: str, k: int | None = None) -> list[tuple[Document, float]]:
    """Return the top-k chunks for a query as (document, relevance_score) pairs.

    Scores are normalised to roughly [0, 1] (higher = more relevant) by Chroma's
    relevance-score helper, and are used by the retrieval guardrail downstream.
    """
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search_with_relevance_scores(query, k=k or settings.top_k)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the policy vector index.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete and recreate the vector store from scratch.",
    )
    args = parser.parse_args()

    count = build_index(rebuild=args.rebuild)
    print(f"Indexed {count} chunks into {settings.vectorstore_dir}")


if __name__ == "__main__":
    main()
