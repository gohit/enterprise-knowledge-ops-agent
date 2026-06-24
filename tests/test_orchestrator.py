"""Unit tests for the Orchestrator agent (ORCH-* cases)."""
from __future__ import annotations

from src.agents.orchestrator import parse_subtasks, plan_query


def test_orch1_multi_part_query_yields_multiple_subtasks(fake_llm):
    llm = fake_llm('{"subtasks": ["rehire rules", "separation conditions"]}')
    plan = plan_query("Can a resigned employee be rehired?", llm)
    assert len(plan) == 2
    assert plan[0].id == "s1" and plan[1].id == "s2"
    assert plan[0].question == "rehire rules"


def test_orch2_simple_query_yields_single_subtask(fake_llm):
    llm = fake_llm('{"subtasks": ["what is the honorarium limit"]}')
    plan = plan_query("What is the honorarium limit?", llm)
    assert len(plan) == 1


def test_orch3_malformed_output_falls_back_to_single_task():
    # No crash on garbage; the whole query becomes one subtask.
    plan = parse_subtasks("this is not json at all", fallback_query="original question")
    assert len(plan) == 1
    assert plan[0].question == "original question"


def test_orch3_json_in_code_fence_is_parsed():
    plan = parse_subtasks('```json\n{"subtasks": ["a", "b"]}\n```', fallback_query="q")
    assert [s.question for s in plan] == ["a", "b"]


def test_empty_subtasks_falls_back():
    plan = parse_subtasks('{"subtasks": []}', fallback_query="fallback q")
    assert len(plan) == 1
    assert plan[0].question == "fallback q"
