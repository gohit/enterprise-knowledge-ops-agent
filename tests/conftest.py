"""Shared test fixtures: a fake LLM and a fake retriever so the agent code can be
tested fully offline (no Azure credentials, no network, deterministic)."""
from __future__ import annotations

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage


class FakeLLM:
    """Minimal stand-in for a chat model.

    ``response`` may be a fixed string, or a callable ``(prompt) -> str`` so one fake
    can return different output for the orchestrator vs the analyst.
    """

    def __init__(self, response="OK"):
        self.response = response
        self.calls: list[str] = []

    def invoke(self, prompt, *args, **kwargs):
        text = prompt if isinstance(prompt, str) else str(prompt)
        self.calls.append(text)
        out = self.response(text) if callable(self.response) else self.response
        return AIMessage(content=out)


@pytest.fixture
def fake_llm():
    return FakeLLM


@pytest.fixture
def routing_llm():
    """A FakeLLM that plays both agents: JSON plan for the orchestrator, prose for the analyst."""

    def _router(prompt: str) -> str:
        if "VERIFIER" in prompt:
            return '{"grounding_score": 0.9, "unsupported_claims": []}'
        if "ORCHESTRATOR" in prompt or "subtask" in prompt.lower():
            return '{"subtasks": ["rehire eligibility", "separation conditions"]}'
        return (
            "A resigned employee may be rehired [Global Rehire Policy.pdf, p.2], "
            "provided they served notice [Global Separation of Employment Policy.pdf, p.4]."
        )

    return FakeLLM(_router)


@pytest.fixture
def low_grounding_llm():
    """Plays all agents, but the Verifier always reports low grounding (drives the limited path)."""

    def _router(prompt: str) -> str:
        if "VERIFIER" in prompt:
            return '{"grounding_score": 0.2, "unsupported_claims": ["unsupported claim"]}'
        if "ORCHESTRATOR" in prompt or "subtask" in prompt.lower():
            return '{"subtasks": ["a question"]}'
        return "An answer that is not well supported [Global Rehire Policy.pdf, p.2]."

    return FakeLLM(_router)


@pytest.fixture
def low_relevance_retriever(sample_chunks):
    """Retriever whose every hit scores below the relevance floor (drives the gate)."""

    def _retrieve(query: str, k=None):
        return [(doc, 0.05) for doc, _ in sample_chunks[: (k or len(sample_chunks))]]

    return _retrieve


@pytest.fixture
def sample_chunks() -> list[tuple[Document, float]]:
    """Two chunks from two different policies, as (document, relevance_score)."""
    return [
        (
            Document(
                page_content="A former employee who resigned voluntarily may be rehired.",
                metadata={"source": "Global Rehire Policy.pdf", "page": 2, "chunk_id": "r::p2::0"},
            ),
            0.81,
        ),
        (
            Document(
                page_content="Employees must serve the full notice period on separation.",
                metadata={"source": "Global Separation of Employment Policy.pdf", "page": 4, "chunk_id": "s::p4::1"},
            ),
            0.74,
        ),
    ]


@pytest.fixture
def fake_retriever(sample_chunks):
    def _retrieve(query: str, k=None):
        return sample_chunks[: (k or len(sample_chunks))]

    return _retrieve
