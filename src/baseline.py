"""Phase 2 — single-agent RAG baseline.

A deliberately simple retrieve-then-answer chain. It is the "basic RAG chatbot"
the case study tells us to surpass; we keep it as a comparison point against the
multi-agent graph (Phase 3+). Both share this module's prompt and citation format.

Dependencies (the retriever and the LLM) are injectable so the baseline can be
unit-tested offline with mocks — no Azure key required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from langchain_core.documents import Document

BASELINE_PROMPT = """You are an enterprise policy assistant. Answer the QUESTION using \
ONLY the CONTEXT below. Cite every fact inline as [source, p.PAGE]. If the context does \
not contain the answer, say you do not have enough information rather than guessing.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""


@dataclass
class BaselineResult:
    answer: str
    sources: list[tuple[str, int]] = field(default_factory=list)


def format_context(chunks: list[Document]) -> str:
    """Render retrieved chunks into a cited context block for the prompt."""
    return "\n\n".join(
        f"[{d.metadata.get('source', '?')}, p.{d.metadata.get('page', '?')}]\n{d.page_content}"
        for d in chunks
    )


def answer_baseline(
    query: str,
    k: int | None = None,
    llm=None,
    retriever: Callable[..., list[tuple[Document, float]]] | None = None,
) -> BaselineResult:
    """Retrieve top-k chunks, prompt the LLM, and return the answer + its sources.

    ``llm`` and ``retriever`` default to the real Azure client and Chroma retriever,
    but can be injected with fakes for offline testing.
    """
    if retriever is None:
        from src.ingestion.index import retrieve as retriever  # lazy: needs creds

    results = retriever(query, k)
    chunks = [doc for doc, _ in results]

    if llm is None:
        from src.llm import get_chat_llm  # lazy: needs creds

        llm = get_chat_llm()

    prompt = BASELINE_PROMPT.format(context=format_context(chunks), question=query)
    response = llm.invoke(prompt)
    answer = getattr(response, "content", str(response))

    sources = [(d.metadata.get("source", "?"), d.metadata.get("page", -1)) for d in chunks]
    return BaselineResult(answer=answer, sources=sources)
