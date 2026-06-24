"""Unit tests for the evaluation & observability layer (EVAL-* cases)."""
from __future__ import annotations

import json

from src.evaluation.metrics import build_report, format_report
from src.evaluation.tracer import save_run
from src.graph.build_graph import run_query


def test_eval1_report_has_required_schema(routing_llm, fake_retriever):
    state = run_query("Can a resigned employee be rehired?", llm=routing_llm, retriever=fake_retriever)
    report = build_report(state)
    for key in ("query", "subtasks", "retrieval", "grounding", "failures", "steps", "agents_invoked"):
        assert key in report
    # One retrieval entry per subtask, each carrying a relevance signal.
    assert len(report["retrieval"]) == report["subtasks"]
    assert all("top_score" in r and "mean_score" in r for r in report["retrieval"])
    assert report["grounding"]["verdict"] == "pass"


def test_eval3_failure_flag_surfaces_in_report(routing_llm, low_relevance_retriever):
    state = run_query("no good matches", llm=routing_llm, retriever=low_relevance_retriever)
    report = build_report(state)
    assert "insufficient_retrieval" in report["failures"]


def test_eval2_save_run_writes_valid_json(tmp_path, routing_llm, fake_retriever):
    state = run_query("Can a resigned employee be rehired?", llm=routing_llm, retriever=fake_retriever)
    path = save_run(state, logs_dir=tmp_path)
    assert path.exists()

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["query"]
    assert payload["final_answer"]
    assert payload["evaluation"]["steps"] >= 5
    assert isinstance(payload["trace"], list) and payload["trace"]
    assert "timestamp" in payload


def test_format_report_is_readable(routing_llm, fake_retriever):
    state = run_query("q", llm=routing_llm, retriever=fake_retriever)
    text = format_report(build_report(state))
    assert "EVALUATION" in text
    assert "Grounding score" in text
    assert "Failures" in text
