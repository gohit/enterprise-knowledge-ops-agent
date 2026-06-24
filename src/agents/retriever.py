"""Retriever agent — RAG.

For each sub-question in the plan, retrieves the top-k chunks (with relevance scores
and source metadata preserved) and records a retrieval signal. Sets ``retrieval_ok``
to False when no subtask found anything above the relevance floor — this drives the
retrieval gate / re-plan loop and the "insufficient retrieval" failure flag.
"""
from __future__ import annotations

from langchain_core.documents import Document

from src.config import settings
from src.graph.state import GraphState, RetrievedChunk


def _to_chunk(doc: Document, score: float) -> RetrievedChunk:
    meta = doc.metadata
    return RetrievedChunk(
        chunk_id=meta.get("chunk_id", ""),
        source=meta.get("source", "?"),
        page=meta.get("page", -1),
        score=float(score),
        text=doc.page_content,
    )


def make_retriever_node(retriever):
    """Build the retriever node bound to a retrieval function ``(query, k) -> [(doc, score)]``."""

    def retriever_node(state: GraphState) -> dict:
        retrieved: dict[str, list[RetrievedChunk]] = {}
        events: list[dict] = []
        any_relevant = False

        for subtask in state["plan"]:
            results = retriever(subtask.question, settings.top_k)
            chunks = [_to_chunk(doc, score) for doc, score in results]
            retrieved[subtask.id] = chunks

            top_score = max((c.score for c in chunks), default=0.0)
            if top_score >= settings.min_relevance:
                any_relevant = True

            events.append(
                {
                    "agent": "retriever",
                    "action": "retrieve",
                    "subtask": subtask.id,
                    "top_score": round(top_score, 3),
                    "chunks": len(chunks),
                    "sources": sorted({c.source for c in chunks}),
                }
            )

        return {"retrieved": retrieved, "retrieval_ok": any_relevant, "trace": events}

    return retriever_node
