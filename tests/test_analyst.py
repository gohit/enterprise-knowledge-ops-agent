"""Unit tests for the Analyst agent (ANA-* cases)."""
from __future__ import annotations

from src.agents.analyst import format_evidence, synthesize
from src.graph.state import RetrievedChunk, SubTask


def _plan_and_evidence(sample_chunks):
    plan = [SubTask(id="s1", question="rehire"), SubTask(id="s2", question="separation")]
    retrieved = {
        "s1": [_rc(sample_chunks[0])],
        "s2": [_rc(sample_chunks[1])],
    }
    return plan, retrieved


def _rc(pair):
    doc, score = pair
    m = doc.metadata
    return RetrievedChunk(m["chunk_id"], m["source"], m["page"], score, doc.page_content)


def test_ana1_evidence_is_grouped_by_subtask(sample_chunks):
    plan, retrieved = _plan_and_evidence(sample_chunks)
    evidence = format_evidence(plan, retrieved)
    assert "Sub-question: rehire" in evidence
    assert "Sub-question: separation" in evidence


def test_ana2_evidence_spans_multiple_documents(sample_chunks):
    plan, retrieved = _plan_and_evidence(sample_chunks)
    evidence = format_evidence(plan, retrieved)
    assert "Global Rehire Policy.pdf" in evidence
    assert "Global Separation of Employment Policy.pdf" in evidence


def test_ana_synthesize_passes_evidence_to_llm(fake_llm, sample_chunks):
    plan, retrieved = _plan_and_evidence(sample_chunks)
    llm = fake_llm("synthesized answer")
    out = synthesize("Can a resigned employee be rehired?", plan, retrieved, llm)
    assert out == "synthesized answer"
    # The evidence text must actually reach the prompt.
    assert "notice period" in llm.calls[0] or "rehired" in llm.calls[0]


def test_ana3_missing_evidence_is_marked(sample_chunks):
    plan = [SubTask(id="s1", question="something"), SubTask(id="s2", question="empty one")]
    retrieved = {"s1": [_rc(sample_chunks[0])], "s2": []}
    evidence = format_evidence(plan, retrieved)
    assert "no relevant evidence found" in evidence
