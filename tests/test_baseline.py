"""Unit tests for the Phase 2 single-agent baseline (offline, mocked)."""
from __future__ import annotations

from langchain_core.documents import Document

from src.baseline import answer_baseline, format_context


def test_format_context_includes_citations():
    docs = [Document(page_content="hello", metadata={"source": "A.pdf", "page": 1})]
    ctx = format_context(docs)
    assert "[A.pdf, p.1]" in ctx
    assert "hello" in ctx


def test_baseline_returns_answer_and_sources(fake_llm, fake_retriever):
    llm = fake_llm("A resigned employee may be rehired [Global Rehire Policy.pdf, p.2].")
    result = answer_baseline(
        "Can a resigned employee be rehired?",
        llm=llm,
        retriever=fake_retriever,
    )
    assert "rehired" in result.answer
    assert ("Global Rehire Policy.pdf", 2) in result.sources
    assert ("Global Separation of Employment Policy.pdf", 4) in result.sources
    assert len(result.sources) == 2


def test_baseline_passes_context_to_llm(fake_llm, fake_retriever):
    """The retrieved context must actually reach the prompt (grounding precondition)."""
    llm = fake_llm("ok")
    answer_baseline("any question", llm=llm, retriever=fake_retriever)
    assert llm.calls, "LLM was never invoked"
    prompt = llm.calls[0]
    assert "notice period" in prompt  # text from a retrieved chunk
    assert "Global Rehire Policy.pdf" in prompt  # citation marker in context


def test_baseline_respects_k(fake_llm, fake_retriever):
    llm = fake_llm("ok")
    result = answer_baseline("q", k=1, llm=llm, retriever=fake_retriever)
    assert len(result.sources) == 1
