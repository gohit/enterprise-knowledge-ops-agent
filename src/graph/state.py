"""Shared graph state — the contract every agent reads from and writes to.

LangGraph threads one ``GraphState`` through all nodes. Fields annotated with the
``add`` reducer (trace, failures, memory) accumulate across nodes; the rest are
overwritten by whichever node produces them. This single object is the backbone of
traceability (the ``trace`` list records every agent action).
"""
from __future__ import annotations

from dataclasses import dataclass
from operator import add
from typing import Annotated, TypedDict


@dataclass
class SubTask:
    """One unit of the Orchestrator's plan."""

    id: str
    question: str


@dataclass
class RetrievedChunk:
    """A retrieved document chunk plus its relevance score and source metadata."""

    chunk_id: str
    source: str
    page: int
    score: float
    text: str


@dataclass
class GroundingReport:
    """The Verifier's assessment of whether the answer is supported by sources."""

    score: float  # fraction of claims supported, 0..1
    verdict: str  # "pass" | "fail"
    unsupported: list[str]


class GraphState(TypedDict, total=False):
    # --- input ---
    query: str
    is_valid: bool

    # --- orchestrator ---
    plan: list[SubTask]
    attempts: int  # bounded re-plan counter

    # --- retriever ---
    retrieved: dict[str, list[RetrievedChunk]]  # subtask_id -> chunks
    retrieval_ok: bool

    # --- analyst ---
    sub_answers: dict[str, str]
    draft_answer: str

    # --- verifier ---
    grounding: GroundingReport

    # --- output ---
    final_answer: str

    # --- observability (accumulated across nodes) ---
    trace: Annotated[list[dict], add]
    failures: Annotated[list[str], add]
    memory: Annotated[list[dict], add]
