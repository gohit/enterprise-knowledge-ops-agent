"""Unit tests for the multi-agent graph routing (GR-* cases). All offline."""
from __future__ import annotations

from src.graph.build_graph import run_query


def _agents_in_trace(state):
    return [e["agent"] for e in state["trace"]]


def test_gr1_happy_path_runs_all_agents(routing_llm, fake_retriever):
    state = run_query("Can a resigned employee be rehired?", llm=routing_llm, retriever=fake_retriever)
    agents = _agents_in_trace(state)
    for expected in ("orchestrator", "retriever", "analyst", "verifier", "memory"):
        assert expected in agents
    assert state["final_answer"]
    assert "rehired" in state["final_answer"]
    assert state["grounding"].verdict == "pass"
    assert not state["failures"]


def test_gr1_plan_has_multiple_subtasks(routing_llm, fake_retriever):
    state = run_query("complex cross-doc question", llm=routing_llm, retriever=fake_retriever)
    assert len(state["plan"]) == 2  # the routing_llm returns two subtasks


def test_gr2_retrieval_gate_abstains_when_irrelevant(routing_llm, low_relevance_retriever):
    state = run_query("question with no good matches", llm=routing_llm, retriever=low_relevance_retriever)
    assert "insufficient_retrieval" in state["failures"]
    assert "enough relevant information" in state["final_answer"]
    # Bounded re-plan: orchestrator should have run more than once before abstaining.
    orchestrator_runs = _agents_in_trace(state).count("orchestrator")
    assert orchestrator_runs >= 2


def test_gr3_low_grounding_returns_limited_answer(low_grounding_llm, fake_retriever):
    state = run_query("a question", llm=low_grounding_llm, retriever=fake_retriever)
    assert "low_grounding" in state["failures"]
    assert "[Note:" in state["final_answer"]  # disclaimer appended
    assert state["grounding"].verdict == "fail"
    # Bounded grounding re-plan: orchestrator ran more than once before giving up.
    assert _agents_in_trace(state).count("orchestrator") >= 2


def test_gr4_invalid_input_routes_to_reject(routing_llm, fake_retriever):
    state = run_query("   ", llm=routing_llm, retriever=fake_retriever)
    assert "invalid_input" in state["failures"]
    assert "could not be processed" in state["final_answer"]
    # Should never reach planning/retrieval.
    assert "orchestrator" not in _agents_in_trace(state)


def test_trace_records_every_step(routing_llm, fake_retriever):
    state = run_query("Can a resigned employee be rehired?", llm=routing_llm, retriever=fake_retriever)
    assert len(state["trace"]) >= 5  # validate, plan, retrieve(s), analyze, memory
    assert state["memory"], "memory agent should record the run"
