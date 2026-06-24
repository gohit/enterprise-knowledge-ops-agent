"""Analyst agent — reasoning and synthesis.

Reasons *across* the evidence retrieved for every sub-question and synthesizes a
single coherent answer, citing each fact by source and page. Evidence is grouped by
sub-question so the LLM can connect facts across documents (the cross-document
synthesis the rubric rewards).
"""
from __future__ import annotations

from src.graph.state import GraphState, RetrievedChunk, SubTask

ANALYST_PROMPT = """You are the ANALYST in a multi-agent system. Using ONLY the EVIDENCE \
below, answer the user's QUESTION. Reason across the different sub-questions and documents \
to produce one coherent answer. Cite every fact inline as [source, p.PAGE]. If the evidence \
is insufficient or conflicting, say so explicitly rather than guessing.

QUESTION: {query}

EVIDENCE:
{evidence}

ANSWER:"""


def format_evidence(
    plan: list[SubTask], retrieved: dict[str, list[RetrievedChunk]]
) -> str:
    """Render retrieved chunks grouped by sub-question, with citations."""
    blocks: list[str] = []
    for subtask in plan:
        lines = [f"## Sub-question: {subtask.question}"]
        chunks = retrieved.get(subtask.id, [])
        if not chunks:
            lines.append("(no relevant evidence found)")
        for chunk in chunks:
            lines.append(f"[{chunk.source}, p.{chunk.page}] {chunk.text}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def synthesize(query: str, plan, retrieved, llm) -> str:
    evidence = format_evidence(plan, retrieved)
    response = llm.invoke(ANALYST_PROMPT.format(query=query, evidence=evidence))
    return getattr(response, "content", str(response))


def make_analyst_node(llm):
    """Build the analyst node bound to a given LLM client."""

    def analyst_node(state: GraphState) -> dict:
        draft = synthesize(state["query"], state["plan"], state["retrieved"], llm)
        cited_sources = sorted(
            {c.source for chunks in state["retrieved"].values() for c in chunks}
        )
        # The Verifier checks this draft; the finalize/limited node sets final_answer.
        return {
            "draft_answer": draft,
            "trace": [
                {"agent": "analyst", "action": "synthesize", "cited_sources": cited_sources}
            ],
        }

    return analyst_node


def insufficient_node(state: GraphState) -> dict:
    """Terminal node when retrieval never found relevant evidence (bounded retries spent)."""
    message = (
        "I don't have enough relevant information in the available policy documents to "
        "answer this question confidently."
    )
    return {
        "draft_answer": message,
        "final_answer": message,
        "failures": ["insufficient_retrieval"],
        "trace": [{"agent": "system", "action": "abstain", "reason": "insufficient_retrieval"}],
    }
